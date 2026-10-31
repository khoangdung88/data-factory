import threading
import zipfile
from io import BytesIO
from itertools import count
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from conftest import DATASETS_DIR, NOW
from datafactory.core.config import Settings
from datafactory.pipeline.runner import RunResult
from datafactory.ui import catalog
from datafactory.ui.app import create_app
from datafactory.ui.jobs import Job, JobManager, JobStatus


@pytest.fixture
def client(settings: Settings) -> TestClient:
    return TestClient(create_app(settings))


def _jobs(app: object) -> JobManager:
    manager: JobManager = app.state.jobs  # type: ignore[attr-defined]
    return manager


def _run(client: TestClient, slug: str = "sample-csv", **form: str) -> Job:
    resp = client.post(f"/datasets/{slug}/run", data=form, follow_redirects=False)
    assert resp.status_code == 303
    job = _jobs(client.app).get(resp.headers["location"].rsplit("/", 1)[-1])
    assert job is not None
    assert job.done.wait(10)
    return job


def _create_app_deterministic(settings: Settings) -> TestClient:
    client = TestClient(create_app(settings))
    ids = count(1)
    manager = _jobs(client.app)
    manager._make_id = lambda: f"job-{next(ids):03d}"
    manager._now = lambda: NOW
    return client


def test_index_lists_datasets_and_invalid_ones(tmp_path: Path) -> None:
    ds = tmp_path / "datasets"
    (ds / "broken").mkdir(parents=True)
    (ds / "broken" / "dataset.yaml").write_text("slug: broken\n")
    (ds / "sample-csv").symlink_to(DATASETS_DIR / "sample-csv")
    client = TestClient(create_app(Settings(data_dir=tmp_path / "data", datasets_dir=ds)))
    body = client.get("/").text
    assert "sample-csv" in body
    assert "invalid dataset" in body


def test_full_run_then_browse_batch_and_product(settings: Settings) -> None:
    client = _create_app_deterministic(settings)
    job = _run(client)
    assert job.id == "job-001"
    assert job.started_at == NOW
    assert job.status == JobStatus.SUCCEEDED, job.error
    assert job.result is not None
    assert job.result.package_dir is not None
    detail = client.get(f"/jobs/{job.id}").text
    assert "succeeded" in detail
    assert "processed" in detail  # job log captured pipeline INFO lines

    page = client.get("/datasets/sample-csv").text
    assert job.result.batch_id in page
    assert "1.0.0" in page

    batch = client.get(f"/datasets/sample-csv/batches/{job.result.batch_id}")
    assert batch.status_code == 200
    assert "quarantine.csv" in batch.text

    product = client.get("/datasets/sample-csv/products/1.0.0")
    assert product.status_code == 200
    assert "Data preview" in product.text

    zipped = client.get("/datasets/sample-csv/products/1.0.0/download")
    assert zipped.headers["content-type"] == "application/zip"
    names = zipfile.ZipFile(BytesIO(zipped.content)).namelist()
    assert "sample-csv-1.0.0/datapackage.json" in names
    assert "sample-csv-1.0.0/data.csv" in names


def test_failed_run_reports_error(client: TestClient) -> None:
    job = _run(client, stage="publish")
    assert job.status == JobStatus.FAILED
    assert job.error is not None
    assert "collect stage first" in job.error
    assert "collect stage first" in client.get(f"/jobs/{job.id}").text


def test_busy_dataset_is_refused() -> None:
    gate = threading.Event()

    def slow_run(slug: str, *a: object) -> RunResult:
        gate.wait(5)
        return RunResult(batch_id="x")

    manager = JobManager(slow_run, now=lambda: NOW)
    first = manager.start("sample-csv", None, None, False)
    with pytest.raises(RuntimeError, match=first.id):
        manager.start("sample-csv", None, None, False)
    other = manager.start("other", None, None, False)
    gate.set()
    assert first.done.wait(5)
    assert other.done.wait(5)


def test_running_job_is_never_evicted() -> None:
    gate = threading.Event()

    def slow_run(slug: str, *a: object) -> RunResult:
        if slug == "held":
            gate.wait(5)
        return RunResult(batch_id="x")

    manager = JobManager(slow_run, now=lambda: NOW)
    held = manager.start("held", None, None, False)
    for _ in range(120):
        done = manager.start("other", None, None, False)
        assert done.done.wait(5)
    with pytest.raises(RuntimeError, match=held.id):
        manager.start("held", None, None, False)  # busy guard still applies
    gate.set()
    assert held.done.wait(5)
    assert manager.get(held.id) is not None


def test_starts_do_not_hang_when_all_slots_busy() -> None:
    release_all = threading.Event()

    def held_run(slug: str, *a: object) -> RunResult:
        release_all.wait(5)
        return RunResult(batch_id=slug)

    manager = JobManager(held_run, now=lambda: NOW)
    jobs = [manager.start(f"ds-{i}", None, None, False) for i in range(110)]
    release_all.set()
    for job in jobs:
        assert job.done.wait(10)
    assert len(manager.list()) <= 100  # finished jobs trimmed when each completes


def test_list_is_newest_first() -> None:
    def instant(slug: str, *a: object) -> RunResult:
        return RunResult(batch_id=slug)

    manager = JobManager(instant, now=lambda: NOW)
    jobs = [manager.start(f"ds-{i}", None, None, False) for i in range(105)]
    for job in jobs:
        assert job.done.wait(5)
    listed = manager.list()
    assert listed[0].slug == jobs[-1].slug
    assert [j.slug for j in listed] == [f"ds-{i}" for i in reversed(range(5, 105))]


@pytest.mark.parametrize(
    "path",
    [
        "/datasets/nope",
        "/datasets/Bad..Slug",
        "/datasets/sample-csv/batches/missing",
        "/datasets/sample-csv/batches/.hidden",
        "/datasets/sample-csv/products/9.9.9",
        "/datasets/sample-csv/products/9.9.9/download",
        "/jobs/missing",
    ],
)
def test_unknown_resources_404(client: TestClient, path: str) -> None:
    assert client.get(path).status_code == 404


def test_unknown_stage_rejected(client: TestClient) -> None:
    resp = client.post("/datasets/sample-csv/run", data={"stage": "bogus"})
    assert resp.status_code == 400


@pytest.mark.parametrize("batch", ["../raw", "a/b", "..", ".env", "x..y"])
def test_unsafe_batch_id_rejected(client: TestClient, batch: str) -> None:
    resp = client.post("/datasets/sample-csv/run", data={"stage": "process", "batch": batch})
    assert resp.status_code == 400


@pytest.mark.parametrize("name", ["..", "../raw", "a/b", ".env", "x..y"])
def test_unsafe_names_rejected(settings: Settings, name: str) -> None:
    with pytest.raises(catalog.NotFoundError):
        catalog.get_batch("sample-csv", name, settings)
    with pytest.raises(catalog.NotFoundError):
        catalog.product_dir("sample-csv", name, settings)


@pytest.mark.parametrize("path", ["tables/data.csv", "a/b/c.csv"])
def test_safe_relpath_accepts_nested(path: str) -> None:
    assert catalog.safe_relpath(path).as_posix() == path


@pytest.mark.parametrize("path", ["../x", "/abs/f.csv", "a/../b", "..", "//srv/f"])
def test_safe_relpath_rejects_traversal(path: str) -> None:
    with pytest.raises(catalog.NotFoundError):
        catalog.safe_relpath(path)


def test_product_zip_stream_contents(tmp_path: Path) -> None:
    root = tmp_path / "products" / "slug" / "1.0.0"
    root.mkdir(parents=True)
    (root / "data.csv").write_text("a\n1\n")
    (root / "datapackage.json").write_text("{}")
    chunks = list(catalog.zip_product("slug", "1.0.0", Settings(data_dir=tmp_path)))
    names = zipfile.ZipFile(BytesIO(b"".join(chunks))).namelist()
    assert names == ["slug-1.0.0/data.csv", "slug-1.0.0/datapackage.json"]

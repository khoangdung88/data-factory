import threading
import zipfile
from io import BytesIO
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from conftest import DATASETS_DIR
from datafactory.core.config import Settings
from datafactory.ui import catalog
from datafactory.ui.app import create_app
from datafactory.ui.jobs import Job, JobManager, JobStatus


@pytest.fixture
def client(settings: Settings) -> TestClient:
    return TestClient(create_app(settings))


def _run(client: TestClient, slug: str = "sample-csv", **form: str) -> Job:
    resp = client.post(f"/datasets/{slug}/run", data=form, follow_redirects=False)
    assert resp.status_code == 303
    jobs: JobManager = client.app.state.jobs  # type: ignore[attr-defined]
    job = jobs.get(resp.headers["location"].rsplit("/", 1)[-1])
    assert job is not None
    assert job.done.wait(10)
    return job


def test_index_lists_datasets_and_invalid_ones(tmp_path: Path) -> None:
    ds = tmp_path / "datasets"
    (ds / "broken").mkdir(parents=True)
    (ds / "broken" / "dataset.yaml").write_text("slug: broken\n")
    (ds / "sample-csv").symlink_to(DATASETS_DIR / "sample-csv")
    client = TestClient(create_app(Settings(data_dir=tmp_path / "data", datasets_dir=ds)))
    body = client.get("/").text
    assert "sample-csv" in body
    assert "invalid dataset" in body


def test_full_run_then_browse_batch_and_product(client: TestClient) -> None:
    job = _run(client)
    assert job.status == JobStatus.SUCCEEDED, job.error
    assert job.result is not None
    assert job.result.package_dir is not None
    assert "succeeded" in client.get(f"/jobs/{job.id}").text

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


def test_busy_dataset_is_refused(settings: Settings) -> None:
    gate = threading.Event()

    def slow_run(*_: object) -> object:
        gate.wait(5)
        raise AssertionError("not reached in assertions")

    manager = JobManager(slow_run)  # type: ignore[arg-type]
    first = manager.start("sample-csv", None, None, False)
    with pytest.raises(RuntimeError, match=first.id):
        manager.start("sample-csv", None, None, False)
    other = manager.start("other", None, None, False)
    gate.set()
    assert first.done.wait(5)
    assert other.done.wait(5)
    assert first.status == JobStatus.FAILED


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


@pytest.mark.parametrize("name", ["..", "../raw", "a/b", ".env", "x..y"])
def test_unsafe_names_rejected(settings: Settings, name: str) -> None:
    with pytest.raises(catalog.NotFoundError):
        catalog.get_batch("sample-csv", name, settings)
    with pytest.raises(catalog.NotFoundError):
        catalog.product_dir("sample-csv", name, settings)

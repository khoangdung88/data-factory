"""FastAPI app: server-rendered pages over ``pipeline.run`` and the data zones."""

from datetime import datetime
from pathlib import Path
from typing import Annotated, Any

from fastapi import APIRouter, FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response, StreamingResponse
from fastapi.templating import Jinja2Templates

from datafactory.contracts.dataset import DatasetSpec, TableSchema
from datafactory.core.config import Settings, get_settings
from datafactory.core.errors import ConfigError
from datafactory.core.logging import configure_logging
from datafactory.pipeline.runner import RunResult, Stage, run
from datafactory.ui import catalog
from datafactory.ui.jobs import DatasetBusyError, JobManager, JobStatus

TEMPLATES = Jinja2Templates(directory=Path(__file__).parent / "templates")
router = APIRouter()


def create_app(settings: Settings | None = None) -> FastAPI:
    resolved = settings or get_settings()
    configure_logging()  # without it the run pages show no INFO logs when serving directly

    def run_fn(
        slug: str, stage: Stage | None, batch_id: str | None, release: bool, now: datetime
    ) -> RunResult:
        return run(
            slug, stage=stage, batch_id=batch_id, release=release, settings=resolved, now=now
        )

    app = FastAPI(title="data-factory", docs_url=None, redoc_url=None, openapi_url=None)
    app.state.settings = resolved
    app.state.jobs = JobManager(run_fn)
    app.add_exception_handler(HTTPException, _http_error)  # type: ignore[arg-type]
    app.include_router(router)
    return app


def _settings(request: Request) -> Settings:
    settings: Settings = request.app.state.settings
    return settings


def _jobs(request: Request) -> JobManager:
    jobs: JobManager = request.app.state.jobs
    return jobs


def _page(request: Request, name: str, status_code: int = 200, **context: Any) -> HTMLResponse:
    return TEMPLATES.TemplateResponse(request, name, context, status_code=status_code)


def _http_error(request: Request, exc: HTTPException) -> HTMLResponse:
    return _page(request, "error.html", status_code=exc.status_code, message=exc.detail)


def _dataset_or_404(slug: str, settings: Settings) -> tuple[DatasetSpec, TableSchema]:
    try:
        return catalog.get_dataset(slug, settings)
    except catalog.NotFoundError as exc:
        raise HTTPException(404, f"dataset {slug!r} not found") from exc


@router.get("/", response_class=HTMLResponse)
def index(request: Request) -> HTMLResponse:
    settings = _settings(request)
    rows = []
    for entry in catalog.list_datasets(settings):
        batches = catalog.list_batches(entry.slug, settings) if entry.spec else []
        products = catalog.list_products(entry.slug, settings) if entry.spec else []
        rows.append((entry, batches[0] if batches else None, products[0] if products else None))
    return _page(request, "index.html", rows=rows, jobs=_jobs(request).list()[:10])


@router.get("/datasets/{slug}", response_class=HTMLResponse)
def dataset(request: Request, slug: str) -> HTMLResponse:
    settings = _settings(request)
    try:
        spec, schema = _dataset_or_404(slug, settings)
    except ConfigError as exc:
        return _page(request, "error.html", status_code=422, message=str(exc))
    return _page(
        request,
        "dataset.html",
        spec=spec,
        schema=schema,
        batches=catalog.list_batches(slug, settings),
        products=catalog.list_products(slug, settings),
        jobs=_jobs(request).list(slug)[:10],
        stages=list(Stage),
    )


@router.post("/datasets/{slug}/run")
def start_run(
    request: Request,
    slug: str,
    stage: Annotated[str, Form()] = "",
    batch: Annotated[str, Form()] = "",
    release: Annotated[bool, Form()] = False,
) -> RedirectResponse:
    try:
        _dataset_or_404(slug, _settings(request))
    except ConfigError as exc:
        raise HTTPException(422, str(exc)) from exc
    try:
        chosen = Stage(stage) if stage else None
        batch_id = catalog.safe_name(batch) if batch else None
    except ValueError as exc:
        raise HTTPException(400, f"unknown stage {stage!r}") from exc
    except catalog.NotFoundError as exc:
        raise HTTPException(400, f"invalid batch id {batch!r}") from exc
    try:
        job = _jobs(request).start(slug, chosen, batch_id, release)
    except DatasetBusyError as exc:
        return RedirectResponse(f"/jobs/{exc.job_id}", status_code=303)
    return RedirectResponse(f"/jobs/{job.id}", status_code=303)


@router.get("/jobs", response_class=HTMLResponse)
def job_list(request: Request) -> HTMLResponse:
    return _page(request, "jobs.html", jobs=_jobs(request).list())


@router.get("/jobs/{job_id}", response_class=HTMLResponse)
def job_detail(request: Request, job_id: str) -> HTMLResponse:
    job = _jobs(request).get(job_id)
    if job is None:
        raise HTTPException(404, f"run {job_id!r} not found")
    return _page(request, "job.html", job=job, running=job.status == JobStatus.RUNNING)


@router.get("/datasets/{slug}/batches/{batch_id}", response_class=HTMLResponse)
def batch(request: Request, slug: str, batch_id: str) -> HTMLResponse:
    settings = _settings(request)
    try:
        entry = catalog.get_batch(slug, batch_id, settings)
    except catalog.NotFoundError as exc:
        raise HTTPException(404, f"batch {batch_id!r} not found") from exc
    staged = catalog.staged_dir(slug, batch_id, settings)
    return _page(
        request,
        "batch.html",
        slug=slug,
        entry=entry,
        data=catalog.preview_csv(staged / "data.csv"),
        quarantine=catalog.preview_csv(staged / "quarantine.csv"),
    )


@router.get("/datasets/{slug}/products/{version}", response_class=HTMLResponse)
def product(request: Request, slug: str, version: str) -> HTMLResponse:
    settings = _settings(request)
    try:
        package = catalog.get_product(slug, version, settings)
        root = catalog.product_dir(slug, version, settings)
    except catalog.NotFoundError as exc:
        raise HTTPException(404, f"product {slug} {version} not found") from exc
    files = sorted(p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file())
    try:
        data = catalog.safe_name(package.resources[0].path) if package.resources else "data.csv"
    except catalog.NotFoundError as exc:
        raise HTTPException(404, f"unsafe resource path {package.resources[0].path!r}") from exc
    return _page(
        request,
        "product.html",
        slug=slug,
        package=package,
        files=files,
        data=catalog.preview_csv(root / data),
    )


@router.get("/datasets/{slug}/products/{version}/download")
def download(request: Request, slug: str, version: str) -> Response:
    try:
        catalog.product_dir(slug, version, _settings(request))  # validated eagerly
        content = catalog.zip_product(slug, version, _settings(request))
    except catalog.NotFoundError as exc:
        raise HTTPException(404, f"product {slug} {version} not found") from exc
    headers = {"Content-Disposition": f'attachment; filename="{slug}-{version}.zip"'}
    return StreamingResponse(content, media_type="application/zip", headers=headers)

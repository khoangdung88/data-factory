"""Command-line interface. Thin adapter: parse args, call pipeline, print result."""

from importlib.metadata import version
from typing import Annotated

import typer

from datafactory.core.config import get_settings
from datafactory.core.errors import DataFactoryError
from datafactory.core.logging import configure_logging
from datafactory.pipeline.runner import Stage, run

app = typer.Typer(no_args_is_help=True, add_completion=False)


@app.callback()
def main() -> None:
    """data-factory: collect, process and publish data products."""


@app.command("version")
def show_version() -> None:
    """Print the installed version."""
    typer.echo(version("datafactory"))


@app.command("run")
def run_dataset(
    slug: str,
    stage: Annotated[Stage | None, typer.Option(help="Run only this stage")] = None,
    batch: Annotated[str | None, typer.Option(help="Batch id (default: latest)")] = None,
    release: Annotated[bool, typer.Option(help="Also run remote publishers")] = False,
) -> None:
    """Run a dataset pipeline (all stages by default)."""
    configure_logging()
    try:
        result = run(slug, stage=stage, batch_id=batch, release=release)
    except DataFactoryError as exc:
        typer.echo(f"error: {exc}", err=True)
        raise typer.Exit(1) from exc
    typer.echo(f"batch: {result.batch_id}")
    if result.package_dir:
        typer.echo(f"package: {result.package_dir}")
    for dest in result.destinations:
        typer.echo(f"published: {dest}")


@app.command("ui")
def serve_ui(
    host: Annotated[
        str, typer.Option(help="Bind address (keep 127.0.0.1 unless trusted)")
    ] = "127.0.0.1",
    port: Annotated[int, typer.Option(help="Port")] = 8000,
) -> None:
    """Start the local web UI."""
    import uvicorn  # noqa: PLC0415

    from datafactory.ui.app import create_app  # noqa: PLC0415

    typer.echo(f"data-factory UI on http://{host}:{port}")
    uvicorn.run(create_app(get_settings()), host=host, port=port)

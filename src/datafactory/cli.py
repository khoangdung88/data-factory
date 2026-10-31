"""Command-line interface. Thin adapter: parse args, call pipeline, print result."""

from importlib.metadata import version

import typer

app = typer.Typer(no_args_is_help=True, add_completion=False)


@app.callback()
def main() -> None:
    """data-factory: collect, process and publish data products."""


@app.command("version")
def show_version() -> None:
    """Print the installed version."""
    typer.echo(version("datafactory"))

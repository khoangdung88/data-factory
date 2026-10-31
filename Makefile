.PHONY: install check fmt test

install:  ## deps + git hooks
	uv sync && uv run pre-commit install

check:    ## everything CI runs
	uv run ruff check .
	uv run ruff format --check .
	uv run mypy
	uv run lint-imports
	uv run pytest -m "not integration"

fmt:      ## auto-format + autofix
	uv run ruff format . && uv run ruff check . --fix

test:
	uv run pytest

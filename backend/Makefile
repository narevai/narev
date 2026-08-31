.PHONY: install format check test dev

install:
	uv sync --group dev

format:
	uv run ruff format .
	uv run ruff check . --fix

check:
	uv run ruff format --check .
	uv run ruff check .

test:
	uv run pytest

dev:
	uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000

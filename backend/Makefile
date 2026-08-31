.PHONY: install format check test dev

install:
	uv pip install --system -e .

format:
	ruff format .
	ruff check . --fix

check:
	ruff format --check .
	ruff check .

test:
	pytest

dev:
	uvicorn main:app --reload --host 0.0.0.0 --port 8000

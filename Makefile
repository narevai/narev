.PHONY: install format check test dev

install:
	uv pip install --system -e . --group dev

format:
	ruff format src tests
	ruff check src tests --fix

check:
	ruff format --check src tests
	ruff check src tests

test:
	pytest

dev:
	python -m varne.app

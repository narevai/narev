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
	pytest --record-mode=none --block-network

dev:
	DEBUG=true LOG_LEVEL=DEBUG python -m varne.app

.PHONY: format lint check test test-cov dev install-dev clean

# Install development dependencies
install-dev:
	pip install -r requirements-dev.txt

# Format code (separate formatting and linting)
format:
	ruff format .

# Auto-fix linting issues
fix:
	ruff check . --fix

fix-unsafe:
	ruff check . --fix --unsafe-fixes

# Lint code (check only, no fixes)
lint:
	ruff check .

# Check formatting and linting (CI-friendly)
check:
	ruff format --check .
	ruff check .

# Run tests
test:
	pytest

# Run tests with coverage
test-cov:
	pytest --cov=. --cov-report=term-missing --cov-report=html

# Clean up generated files
clean:
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf .pytest_cache/
	find . -type d -name __pycache__ -exec rm -rf {} +

# Run development server
dev:
	uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Format and fix everything (convenience target)
format-all: format fix

up:
	docker-compose -f ../.devcontainer/docker-compose.yaml up -d --build

down:
	docker-compose -f ../.devcontainer/docker-compose.yaml down

start-mock-server:
	python tests/mock_api/server.py

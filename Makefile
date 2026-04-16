# Quell — developer convenience targets
#
# Requires GNU Make. On Windows, install via:
#   choco install make   (Chocolatey)
#   scoop install make   (Scoop)
# Alternatively, run the Poetry commands directly.

.PHONY: install test lint typecheck build run clean

## install: Install all dependencies via Poetry
install:
	poetry install

## test: Run the full test suite with coverage
test:
	poetry run pytest --cov=quell --cov-report=term-missing -v

## lint: Check and format code with Ruff
lint:
	poetry run ruff check quell/ tests/
	poetry run ruff format --check quell/ tests/

## typecheck: Run mypy strict type checking
typecheck:
	poetry run mypy quell/

## build: Build the wheel and sdist
build:
	poetry build

## run: Run the CLI
run:
	poetry run quell

## clean: Remove build artifacts and caches
clean:
	rm -rf dist/ build/ .mypy_cache/ .ruff_cache/ .pytest_cache/ htmlcov/ .coverage
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true

## help: Show this help
help:
	@grep -E '^## ' Makefile | sed 's/^## //'

.PHONY: help setup install test lint format run demo clean

help:
	@echo "AI Chemistry Video Request Service - Reviewer Makefile"
	@echo ""
	@echo "Available commands:"
	@echo "  make setup     Create .venv and install dependencies"
	@echo "  make test      Run full pytest test suite (45 tests)"
	@echo "  make lint      Run Ruff linter and format checks"
	@echo "  make format    Format code with Ruff"
	@echo "  make run       Start FastAPI service on http://localhost:8000"
	@echo "  make demo      Generate and stream videos via the live REST API"
	@echo "  make clean     Clean temporary caches"

setup: install

install:
	@command -v uv >/dev/null 2>&1 || { echo "Installing uv..."; curl -LsSf https://astral.sh/uv/install.sh | sh; }
	uv venv --python 3.12 .venv
	uv pip install -e ".[dev]"
	@if [ ! -f .env ]; then cp .env.example .env; echo "Created .env from .env.example"; fi

test:
	uv run --python .venv pytest -v

lint:
	uv run --python .venv ruff check .
	uv run --python .venv ruff format --check .

format:
	uv run --python .venv ruff format .

run:
	uv run --python .venv uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

demo:
	uv run --python .venv python -m scripts.generate_via_api

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
	rm -rf build/ dist/ *.egg-info

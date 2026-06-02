.PHONY: install dev agent api test lint clean

install:
	uv sync

dev: install
	uv run uvicorn backend.main:app --reload --port 8080

agent:
	uv run adk web app

api:
	uv run uvicorn backend.main:app --reload --port 8080

test:
	uv run pytest tests/ -v

lint:
	uv run ruff check .
	uv run ruff format --check .

format:
	uv run ruff check --fix .
	uv run ruff format .

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache dist build *.egg-info

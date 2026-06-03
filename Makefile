.PHONY: install dev api frontend agent test lint clean

install:
	uv sync

dev: install
	@echo "Starting backend on :8080 and frontend on :5173..."
	@trap 'kill 0' INT TERM; \
	uv run uvicorn backend.main:app --reload --port 8080 --env-file .env & \
	cd frontend && npx vite & \
	wait

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

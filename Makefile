.PHONY: help init test lint run

ifeq ($(OS),Windows_NT)
	LINK_SKILLS := powershell -ExecutionPolicy Bypass -File scripts/link-skills.ps1
else
	LINK_SKILLS := bash scripts/link-skills.sh
endif

help:
	@echo "Available commands:"
	@echo "  make init   - Setup local dependencies and link vendored skills"
	@echo "  make test   - Run unit and integration tests"
	@echo "  make lint   - Run static analysis and linting"
	@echo "  make run    - Run local application"

init:
	@echo "Installing dependencies..."
	uv sync
	git submodule update --init --recursive
	$(LINK_SKILLS)

test:
	uv run pytest

lint:
	uv run ruff check .
	uv run ruff format --check .

run:
	uv run streamlit run src/api/app.py

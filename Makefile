.PHONY: test lint fmt serve install coverage

install:
	pip install -e ".[dev]"

test:
	pytest

lint:
	ruff check src/ tests/
	black --check --diff .

fmt:
	black .
	isort src/ tests/

serve:
	python -m src.apps.server.main

coverage:
	pytest --cov=src --cov-report=html
	@echo "Coverage report: htmlcov/index.html"

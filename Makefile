.PHONY: install test lint fmt check serve coverage build docker

install:
	pip install -e ".[dev]"
	pre-commit install || true

test:
	pytest

lint:
	ruff check src tests scripts
	black --check --diff src tests scripts

fmt:
	isort src tests scripts
	black src tests scripts

check: lint test

serve:
	testio-server

coverage:
	pytest --cov --cov-report=html
	@echo "Coverage report: htmlcov/index.html"

build:
	python -m build

docker:
	docker build -t testio .

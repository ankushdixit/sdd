.PHONY: help install test lint format clean build

help:
	@echo "SDD - Session-Driven Development"
	@echo ""
	@echo "Available targets:"
	@echo "  help      - Show this help message"
	@echo "  install   - Install dependencies"
	@echo "  test      - Run test suite"
	@echo "  lint      - Run linting (ruff + bandit)"
	@echo "  format    - Format code with ruff"
	@echo "  clean     - Remove build artifacts and caches"
	@echo "  build     - Build distribution packages"

install:
	pip install -e .
	pip install -r requirements.txt

test:
	pytest tests/ -v

lint:
	ruff check .
	bandit -r scripts/ sdd_cli.py

format:
	ruff check --fix .
	ruff format .

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf .pytest_cache/
	rm -rf .ruff_cache/
	rm -rf htmlcov/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name ".coverage" -delete
	find . -type f -name "coverage.xml" -delete
	find . -type f -name "coverage.json" -delete

build:
	python setup.py sdist bdist_wheel

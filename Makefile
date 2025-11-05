# AI Attendance System - Development Tools

.PHONY: help install format lint type-check test clean

help:
	@echo "Available commands:"
	@echo "  install      - Install development dependencies"
	@echo "  format       - Format code with black and isort"
	@echo "  lint         - Run ruff linter"
	@echo "  type-check   - Run mypy type checking"
	@echo "  test         - Run test suite"
	@echo "  quality      - Run all code quality checks"
	@echo "  clean        - Clean up cache files"

install:
	pip install black isort ruff mypy pytest pytest-cov

format:
	black src/ ui/ tests/
	isort src/ ui/ tests/

lint:
	ruff check src/ ui/ tests/

type-check:
	mypy src/ ui/

test:
	python run_tests.py

quality: format lint type-check test

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type d -name "*.pyc" -delete
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
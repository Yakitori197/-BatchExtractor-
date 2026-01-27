.PHONY: install dev test lint format typecheck clean build check-7z help

# Default target
help:
	@echo "unpack-flat development commands:"
	@echo ""
	@echo "  make install     Install package"
	@echo "  make dev         Install with dev dependencies"
	@echo "  make test        Run tests"
	@echo "  make lint        Run linter"
	@echo "  make format      Format code"
	@echo "  make typecheck   Run type checker"
	@echo "  make check-7z    Check 7-Zip availability"
	@echo "  make clean       Clean build artifacts"
	@echo "  make build       Build distribution"
	@echo ""

# Install package
install:
	pip install -e .

# Install with development dependencies
dev:
	pip install -e ".[dev]"

# Run tests
test:
	pytest tests/ -v

# Run tests with coverage
test-cov:
	pytest tests/ -v --cov=unpack_flat --cov-report=html --cov-report=term

# Run linter
lint:
	ruff check src/ tests/

# Format code
format:
	ruff format src/ tests/
	ruff check --fix src/ tests/

# Run type checker
typecheck:
	mypy src/unpack_flat

# Check 7-Zip availability
check-7z:
	unpack-flat --check-7z

# Clean build artifacts
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf src/*.egg-info/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

# Build distribution
build: clean
	pip install build
	python -m build

# Run all checks
all: lint typecheck test
	@echo "All checks passed!"

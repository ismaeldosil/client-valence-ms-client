.PHONY: lint test type-check security all pre-push find-gaps generate-tests mutation install-hooks

# Linting and formatting
lint:
	ruff check src/ tests/ --fix
	ruff format src/ tests/

# Run tests with coverage
test:
	pytest --cov=src --cov-report=html --cov-branch

# Type checking
type-check:
	mypy src/

# Security scan
security:
	bandit -r src/ -f html -o reports/bandit-report.html

# Mutation testing (takes longer)
mutation:
	mutmut run --paths-to-mutate=src/teams --tests-dir=tests/

# Pre-push: full static analysis before push
pre-push:
	@echo "=== Full Static Analysis (Pre-Push) ==="
	@echo "1/4: Linting..."
	ruff check src/ tests/
	@echo "2/4: Type checking..."
	mypy src/
	@echo "3/4: Security scan..."
	bandit -r src/ -ll -q
	@echo "4/4: Running tests..."
	pytest --cov=src --cov-fail-under=70 -q
	@echo "All checks passed! Safe to push."

# Identify code without tests
find-gaps:
	python scripts/find_untested_code.py

# Generate tests with Qodo AI (if installed)
generate-tests:
	qodo generate src/ --output tests/generated/

# Install pre-commit and pre-push hooks
install-hooks:
	pre-commit install
	pre-commit install --hook-type pre-push

# Run all quality checks
all: lint type-check security test

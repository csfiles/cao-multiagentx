.PHONY: install install-dev lint format test test-cov mcp-server demo health clean setup

# Default target
help:
	@echo "SupportMesh — available targets:"
	@echo "  make setup        Install deps and copy .env.example"
	@echo "  make install      Install package (production)"
	@echo "  make install-dev  Install package with dev dependencies"
	@echo "  make mcp-server   Start the MCP customer-support server"
	@echo "  make demo         Run the multi-agent demo"
	@echo "  make health       Check system health"
	@echo "  make test         Run all tests"
	@echo "  make test-cov     Run tests with coverage summary"
	@echo "  make lint         Run ruff + mypy"
	@echo "  make format       Auto-format with ruff"
	@echo "  make clean        Remove build artifacts"

setup:
	@cp -n .env.example .env 2>/dev/null || echo ".env already exists"
	uv pip install -e ".[dev]"
	@echo "Setup complete. Edit .env if needed, then: make mcp-server"

install:
	uv pip install -e .

install-dev:
	uv pip install -e ".[dev]"

lint:
	python -m ruff check app/ mcp/ workflows/ tests/
	python -m mypy app/ mcp/ workflows/ --ignore-missing-imports

format:
	python -m ruff format app/ mcp/ workflows/ tests/
	python -m ruff check --fix app/ mcp/ workflows/ tests/

test:
	python -m pytest tests/ -v

test-cov:
	python -m pytest tests/ -v --tb=short

mcp-server:
	python -m mcp.customer_support_server.server

demo:
	python -m app.cli demo

health:
	python -m app.cli health

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
	rm -rf .pytest_cache .mypy_cache .ruff_cache dist build *.egg-info

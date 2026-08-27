.PHONY: install test lint fmt check demo clean

install:
	uv pip install -e ".[dev]"

test:
	uv run pytest tests/ -v

lint:
	uv run ruff check src/ tests/

fmt:
	uv run ruff format src/ tests/

check: lint test

demo:
	@echo "=== CAO CLI Demo (mock provider) ==="
	@echo "Listing agent profiles:"
	uv run cao agents
	@echo ""
	@echo "Running inventory specialist (mock):"
	uv run cao run agents/inventory_specialist.md \
		--input "Check order ORD-1001" \
		--provider mock

clean:
	rm -rf .venv __pycache__ dist build .pytest_cache .ruff_cache
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true

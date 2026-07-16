.PHONY: sync install lint format typecheck test test-network check security run docker-up docker-down smithery pre-commit clean

sync install:
	uv sync --extra dev

lint:
	uv run ruff check .

format:
	uv run ruff format .

typecheck:
	uv run ty check

test:
	uv run pytest -m "not network"

test-network:
	uv run pytest -m network

check: lint
	uv run ruff format --check .
	$(MAKE) typecheck
	$(MAKE) test

security:
	uv run pip-audit
	uv run bandit -r helpers tools main.py asgi.py -q -c pyproject.toml
	uv run detect-secrets scan --baseline .secrets.baseline --exclude-files '(^|/)\.venv/|(^|/)uv\.lock$$|(^|/)\.git/'


run:
	uv run python main.py

docker-up:
	docker compose up -d --build

docker-down:
	docker compose down

smithery:
	@echo "Smithery config: smithery.yaml"
	@echo "Deploy: https://smithery.ai — publish this repo with Streamable HTTP on /mcp"
	@if command -v npx >/dev/null 2>&1; then \
		npx --yes @smithery/cli@latest --help 2>/dev/null | head -n 20 || true; \
	else \
		echo "npx not found; install Node.js to use @smithery/cli locally."; \
	fi

pre-commit:
	uv run pre-commit run --all-files

clean:
	@echo "Removing caches, build artifacts, and local runtime state..."
	rm -rf __pycache__ .pytest_cache .ruff_cache .mypy_cache .ty .coverage htmlcov dist build .eggs *.egg-info
	rm -rf .superpowers .cursor/hooks/state
	find . -type d -name '__pycache__' -not -path './.venv/*' -exec rm -rf {} + 2>/dev/null || true
	find . -type f \( -name '*.py[cod]' -o -name '*$$py.class' -o -name '*.tmp' -o -name '*.bak' -o -name '*.orig' \) -not -path './.venv/*' -delete 2>/dev/null || true
	rm -f _version.py

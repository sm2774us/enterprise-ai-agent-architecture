.PHONY: install test lint fmt build up down precommit

SERVICES := agent-orchestrator control-tower mcp-a2a-gateway llm-gateway

install:
	@for s in $(SERVICES); do \
		echo "==> installing $$s"; \
		python3 -m venv services/$$s/.venv; \
		services/$$s/.venv/bin/pip install -q --upgrade pip; \
		services/$$s/.venv/bin/pip install -q -e "services/$$s[dev]"; \
	done

test:
	@for s in $(SERVICES); do \
		echo "==> testing $$s"; \
		(cd services/$$s && .venv/bin/pytest -q) || exit 1; \
	done

lint:
	@for s in $(SERVICES); do \
		echo "==> linting $$s"; \
		(cd services/$$s && .venv/bin/ruff check app tests && .venv/bin/mypy app) || exit 1; \
	done

fmt:
	@for s in $(SERVICES); do \
		(cd services/$$s && .venv/bin/ruff format app tests); \
	done

precommit:
	pre-commit run --all-files

build:
	docker compose build

up:
	docker compose up --build

down:
	docker compose down -v

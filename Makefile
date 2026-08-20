PYTHON ?= python
COVERAGE_MIN ?= 55
IMAGE ?= demandpulse-api

.PHONY: install test train lint format format-check typecheck security docker-build docker-up docker-down smoke load-test ci

install:
	$(PYTHON) -m pip install -e ".[dev]"

test:
	$(PYTHON) -m pytest -v --cov=demandpulse --cov-report=term-missing --cov-fail-under=$(COVERAGE_MIN)

train:
	$(PYTHON) -m demandpulse.cli train --sample-percent $${SERIES_SAMPLE_PERCENT:-30}

lint:
	$(PYTHON) -m ruff check src tests

format:
	$(PYTHON) -m ruff format src tests

format-check:
	$(PYTHON) -m ruff format --check src tests

typecheck:
	$(PYTHON) -m mypy \
		src/demandpulse/api \
		src/demandpulse/data/loader.py \
		src/demandpulse/forecasting/point_model.py \
		src/demandpulse/forecasting/probabilistic.py \
		src/demandpulse/optimization/inventory.py

security:
	$(PYTHON) -m pip_audit --strict --skip-editable

smoke:
	$(PYTHON) scripts/smoke_test.py --base-url $${BASE_URL:-http://127.0.0.1:8000}

load-test:
	$(PYTHON) scripts/load_test.py --base-url $${BASE_URL:-http://127.0.0.1:8000} --endpoint $${LOAD_TEST_ENDPOINT:-/health} --requests $${LOAD_TEST_REQUESTS:-50}

docker-build:
	docker build \
		--build-arg APP_VERSION=$${APP_VERSION:-0.3.0} \
		--build-arg VCS_REF=$${GIT_COMMIT:-$$(git rev-parse --short HEAD 2>/dev/null || echo local)} \
		--build-arg SOURCE_URL=$${SOURCE_REPOSITORY:-local} \
		-t $(IMAGE) .

docker-up:
	docker compose up --build -d

docker-down:
	docker compose down

ci: lint format-check typecheck test security

.PHONY: install migrate run lint test docker-build docker-up docker-down

install:
	pip install -r requirements-dev.txt

migrate:
	alembic upgrade head

run: migrate
	uvicorn tickethub.main:app --reload --app-dir src

lint:
	ruff check .

test:
	pytest -q

docker-build:
	docker build -t tickethub .

docker-up:
	docker compose up --build

docker-down:
	docker compose down

docs:
	python scripts/export_openapi.py	
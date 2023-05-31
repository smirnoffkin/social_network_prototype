env:
	@$(eval SHELL:=/bin/bash)
	@cp .env.example .env
	@echo "SECRET_KEY=$$(openssl rand -hex 32)" >> .env

dev:
	pip install -r requirements.txt

lint:
	flake8 ./app/

test:
	pytest -v ./tests/

run:
	uvicorn app.main:app --host=0.0.0.0 --port=8080 --reload

makemigrations:
	alembic init migrations

revision:
	alembic revision --autogenerate

migrate:
	alembic upgrade head

up-dev:
	docker-compose -f dev.docker-compose.yml up -d

down-dev:
	docker-compose -f dev.docker-compose.yml down

build-prod:
	docker-compose build

up-prod:
	docker-compose -f prod.docker-compose.yml up -d --build

down-prod:
	docker-compose -f prod.docker-compose.yml down

run-prod:
	make migrate
	make run

up-celery:
	celery -A app.utils.celery.worker:celery worker --loglevel=INFO --pool=solo

up-redis:
	docker run -d --name redis -p 6379:6379 redis:alpine

down-redis:
	docker stop redis
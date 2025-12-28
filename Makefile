.PHONY: help build up down restart logs clean migrate seed test

help:
	@echo "Database AI - Available commands:"
	@echo "  make build      - Build all Docker images"
	@echo "  make up         - Start all services"
	@echo "  make down       - Stop all services"
	@echo "  make restart    - Restart all services"
	@echo "  make logs       - View logs"
	@echo "  make migrate    - Run database migrations"
	@echo "  make seed       - Seed database with test data"
	@echo "  make clean      - Remove all containers and volumes"
	@echo "  make test       - Run tests"

build:
	docker-compose build

up:
	docker-compose up -d

up-full:
	docker-compose --profile replica --profile ha --profile monitoring up -d

down:
	docker-compose down

restart:
	docker-compose restart

logs:
	docker-compose logs -f

logs-api:
	docker-compose logs -f api

logs-celery:
	docker-compose logs -f celery_worker_email celery_worker_parsing

clean:
	docker-compose down -v
	docker system prune -f

migrate:
	docker-compose exec api alembic upgrade head

migrate-create:
	docker-compose exec api alembic revision --autogenerate -m "$(name)"

seed:
	docker-compose exec api python -m app.cli seed_db

create-admin:
	docker-compose exec api python -m app.cli create_admin

shell:
	docker-compose exec api python

db-shell:
	docker-compose exec postgres_master psql -U $(POSTGRES_USER) -d $(POSTGRES_DB)

test:
	docker-compose exec api pytest

init:
	cp .env.example .env
	@echo "Please edit .env file with your configuration"

.PHONY: help install dev-setup start stop restart logs test clean

help:
	@echo "Market Research SaaS - Development Commands"
	@echo ""
	@echo "  make install      - Install dependencies"
	@echo "  make dev-setup    - Setup development environment"
	@echo "  make start        - Start all services"
	@echo "  make stop         - Stop all services"
	@echo "  make restart      - Restart all services"
	@echo "  make logs         - View logs"
	@echo "  make test         - Run tests"
	@echo "  make init-db      - Initialize database"
	@echo "  make clean        - Clean up containers and volumes"
	@echo ""

install:
	pip install -r requirements.txt

dev-setup:
	@echo "Setting up development environment..."
	cp .env.example .env
	@echo "Please edit .env with your API keys"

start:
	docker-compose up -d

stop:
	docker-compose down

restart:
	docker-compose restart

logs:
	docker-compose logs -f

test:
	pytest

test-cov:
	pytest --cov=app --cov-report=html --cov-report=term

init-db:
	docker-compose exec api python scripts/init_db.py

clean:
	docker-compose down -v
	rm -rf __pycache__ .pytest_cache .mypy_cache .coverage htmlcov
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

format:
	black app tests

lint:
	flake8 app tests
	mypy app
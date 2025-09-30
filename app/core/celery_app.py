"""Celery application configuration"""
from celery import Celery
from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "market_research",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    # include=["app.tasks"]  # Commented out - no tasks module yet
)

# Optional configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

if __name__ == "__main__":
    celery_app.start()
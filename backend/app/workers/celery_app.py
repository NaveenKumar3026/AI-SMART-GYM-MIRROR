from celery import Celery
from app.core.config import settings

celery = Celery(
    "workers",
    broker=settings.CELERY_BROKER_URL or settings.REDIS_URL,
    backend=settings.CELERY_RESULT_BACKEND or settings.REDIS_URL,
)

celery.conf.task_routes = {}

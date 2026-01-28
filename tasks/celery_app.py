from celery import Celery
from bot.config import settings

celery_app = Celery(
    'youtube_downloader',
    broker=settings.celery_broker,
    backend=settings.celery_backend,
    include=['tasks.download']
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Europe/Moscow',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=settings.download_timeout,
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=10,
)

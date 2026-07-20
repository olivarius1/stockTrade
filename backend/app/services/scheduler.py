from celery import Celery
from celery.schedules import crontab
from app.core.config import settings

celery_app = Celery(
    "valuation",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.tasks.valuation_tasks"],
)

celery_app.conf.beat_schedule = {
    'daily-valuation': {
        'task': 'app.tasks.valuation_tasks.calculate_watchlist',
        'schedule': crontab(hour=18, minute=0),
    },
    'daily-data-update': {
        'task': 'app.tasks.valuation_tasks.update_kline_and_recalculate',
        'schedule': crontab(hour=3, minute=0),
    },
    'daily-kline-batch-fetch': {
        'task': 'app.tasks.valuation_tasks.kline_batch_fetch',
        'schedule': crontab(hour=16, minute=30),
    },
}

celery_app.conf.timezone = 'Asia/Shanghai'

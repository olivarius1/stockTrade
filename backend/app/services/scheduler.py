from celery import Celery
from celery.schedules import crontab
from app.core.config import settings

celery_app = Celery(
    "valuation",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

celery_app.conf.beat_schedule = {
    'daily-valuation': {
        'task': 'app.tasks.valuation_tasks.calculate_watchlist',
        'schedule': crontab(hour=18, minute=0),
    },
}

celery_app.conf.timezone = 'Asia/Shanghai'

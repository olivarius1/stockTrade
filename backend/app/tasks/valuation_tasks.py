from app.services.scheduler import celery_app
from app.services.watchlist import WatchlistService
from app.db.session import SessionLocal


@celery_app.task
def calculate_watchlist():
    db = SessionLocal()
    try:
        service = WatchlistService()
        results = service.batch_calculate(db)
        return {"results": results}
    finally:
        db.close()

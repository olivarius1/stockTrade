from .session import engine, Base, get_db
from .models import KlineData, ValuationHistory, FinancialData, Watchlist, StockGroup, SchedulerConfig, ModelConfig, User, TaskProgress

def init_db():
    Base.metadata.create_all(bind=engine)

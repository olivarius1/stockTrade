"""快速检查数据库各表数据量。"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import SessionLocal
from app.db.models import Watchlist, ValuationHistory, KlineData, StockGroup

db = SessionLocal()
print(f"watchlist: {db.query(Watchlist).count()}")
print(f"valuation_history: {db.query(ValuationHistory).count()}")
print(f"kline_data: {db.query(KlineData).count()}")
print(f"stock_group: {db.query(StockGroup).count()}")
db.close()

"""诊断：检查各表数据量和K线/估值历史状态。"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings
print(f"DB URL: {settings.DATABASE_URL}")

from app.db.session import SessionLocal
from app.db.models import KlineData, ValuationHistory, Watchlist
from sqlalchemy import func

db = SessionLocal()
print(f"watchlist: {db.query(Watchlist).count()}")
print(f"kline_data: {db.query(KlineData).count()}")
print(f"valuation_history: {db.query(ValuationHistory).count()}")

# 每只股票的K线和估值历史条数
stocks = db.query(Watchlist.stock_code, Watchlist.stock_name).all()
for code, name in stocks[:10]:
    kline_cnt = db.query(KlineData).filter(KlineData.stock_code == code).count()
    val_cnt = db.query(ValuationHistory).filter(ValuationHistory.stock_code == code).count()
    print(f"  {code} {name}: kline={kline_cnt}, valuation={val_cnt}")

db.close()

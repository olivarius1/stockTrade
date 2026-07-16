from app.services.scheduler import celery_app
from app.services.watchlist import WatchlistService
from app.db.session import SessionLocal
from app.db.models import Watchlist, KlineData, ValuationHistory
from app.data.kline_manager import update_kline
from app.core.cache import cache_clear_pattern
from datetime import date


@celery_app.task
def calculate_watchlist():
    db = SessionLocal()
    try:
        service = WatchlistService()
        results = service.batch_calculate(db)
        return {"results": results}
    finally:
        db.close()


@celery_app.task
def update_kline_and_recalculate():
    db = SessionLocal()
    try:
        watchlist_items = db.query(Watchlist).all()
        results = []
        
        for item in watchlist_items:
            stock_code = item.stock_code
            stock_name = item.stock_name
            
            try:
                added, total, latest = update_kline(stock_code)
                
                if added > 0:
                    # K线数据更新后清除该股票的衍生计算缓存（MA、波动率等），
                    # 避免下次计算使用过期结果
                    cache_clear_pattern(f"calc:*:{stock_code}:*")
                    service = WatchlistService()
                    kline_data = service.data_service.get_kline_data(stock_code, db=db)
                    
                    if kline_data:
                        stock_info = kline_data[0]
                        historical = kline_data[1:]
                        
                        price = stock_info.get("price", 0)
                        pe = stock_info.get("pe", 0)
                        pb = stock_info.get("pb", 0)
                        volume = stock_info.get("volume", 0)
                        
                        closes = [h["close"] for h in historical if h.get("close") is not None]
                        ma20 = service.data_service.calculate_ma(stock_code, closes, period=20)
                        ma60 = service.data_service.calculate_ma(stock_code, closes, period=60)
                        volatility = service.data_service.calculate_volatility(stock_code, closes)
                        
                        volumes = [h["volume"] for h in historical if h.get("volume") is not None]
                        avg_volume = sum(volumes) / len(volumes) if volumes else 1
                        volume_ratio = volume / avg_volume if avg_volume else 1
                        
                        financial = service.data_service.get_financial_data(stock_code, db=db)
                        
                        data = {
                            "price": price,
                            "pe": pe,
                            "pb": pb,
                            "volume": volume,
                            "amount": stock_info.get("amount", 0),
                            "ma20": ma20,
                            "ma60": ma60,
                            "volatility": volatility,
                            "volume_ratio": volume_ratio,
                            "eps": financial.get("eps", 0),
                            "revenue": financial.get("revenue", 0),
                            "net_profit": financial.get("net_profit", 0),
                            "roe": financial.get("roe", 0),
                            "gross_margin": financial.get("gross_margin", 0),
                            "dividend_rate": financial.get("dividend_rate", 0),
                        }
                        
                        result = service.valuation_service.calculate(
                            stock_code, item.model_type, data, ai_enabled=item.ai_enabled
                        )
                        
                        factors = result.get("factors", {})
                        score = result.get("score", 0)

                        service.save_valuation_history(
                            db, stock_code, date.today(), score, factors, pe, pb, price
                        )
                        
                        results.append({
                            "stock_code": stock_code,
                            "stock_name": stock_name,
                            "added_days": added,
                            "total_days": total,
                            "recalculated": True,
                            "score": score,
                        })
                    else:
                        results.append({
                            "stock_code": stock_code,
                            "stock_name": stock_name,
                            "added_days": added,
                            "total_days": total,
                            "recalculated": False,
                            "error": "No kline data available",
                        })
                else:
                    results.append({
                        "stock_code": stock_code,
                        "stock_name": stock_name,
                        "added_days": added,
                        "total_days": total,
                        "recalculated": False,
                        "reason": "No new data",
                    })
                    
            except Exception as e:
                db.rollback()
                results.append({
                    "stock_code": stock_code,
                    "stock_name": stock_name,
                    "added_days": 0,
                    "total_days": 0,
                    "recalculated": False,
                    "error": str(e),
                })
        
        return {"results": results}
    finally:
        db.close()

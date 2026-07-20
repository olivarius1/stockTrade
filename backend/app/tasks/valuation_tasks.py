from app.services.scheduler import celery_app
from app.services.watchlist import WatchlistService
from app.db.session import SessionLocal
from app.db.models import Watchlist, KlineData, ValuationHistory, TaskProgress
from app.data.kline_manager import update_kline
from app.core.cache import cache_clear_pattern, cache_get, cache_set, redis_client
from datetime import date, datetime
import json
import logging

logger = logging.getLogger(__name__)

# Redis key 常量
KLINE_TASK_LOCK = "task:kline_batch:lock"
KLINE_TASK_PROGRESS = "task:kline_batch:progress"


@celery_app.task
def calculate_watchlist():
    db = SessionLocal()
    try:
        service = WatchlistService()
        results = service.batch_calculate(db)
        return {"results": results}
    finally:
        db.close()


@celery_app.task(bind=True)
def kline_batch_fetch(self):
    """全市场K线批量获取 + 估值历史填充。

    流程：
    1. 获取所有自选股列表
    2. 逐只拉取K线数据（update_kline）
    3. 对估值历史不足的股票执行 backfill
    4. 通过 Redis 实时报告进度，完成后写入 PG 持久化
    """
    # 防重复触发：Redis 锁
    if redis_client:
        if not redis_client.set(KLINE_TASK_LOCK, "1", nx=True, ex=3600):
            return {"status": "already_running", "message": "任务已在执行中"}
    else:
        # 无Redis时用内存检查（降级）
        if cache_get(KLINE_TASK_LOCK):
            return {"status": "already_running", "message": "任务已在执行中"}
        cache_set(KLINE_TASK_LOCK, "1", expire_seconds=3600)

    db = SessionLocal()
    try:
        watchlist_items = db.query(Watchlist).all()
        total = len(watchlist_items)

        # 创建 PG 进度记录
        progress_record = TaskProgress(
            task_type="kline_batch_fetch",
            status="running",
            total=total,
            completed=0,
            failed=0,
        )
        db.add(progress_record)
        db.commit()
        db.refresh(progress_record)

        service = WatchlistService()
        completed = 0
        failed = 0
        errors = []

        for idx, item in enumerate(watchlist_items):
            stock_code = item.stock_code
            stock_name = item.stock_name
            try:
                # 1. 拉取K线数据
                update_kline(stock_code)
                db.expire_all()

                # 2. 检查估值历史是否充足，不足则backfill
                history_count = db.query(ValuationHistory).filter(
                    ValuationHistory.stock_code == stock_code
                ).count()
                if history_count < 30:
                    service.backfill_valuation_history(
                        db, stock_code, item.model_type, item.ai_enabled
                    )

                cache_clear_pattern(f"calc:*:{stock_code}:*")
                completed += 1

            except Exception as e:
                db.rollback()
                failed += 1
                errors.append({"stock_code": stock_code, "stock_name": stock_name, "error": str(e)})
                logger.error(f"kline_batch_fetch failed for {stock_code}: {e}")

            # 更新 Redis 实时进度
            progress_data = json.dumps({
                "task_id": progress_record.id,
                "total": total,
                "completed": completed,
                "failed": failed,
                "current": stock_name,
                "status": "running",
            })
            if redis_client:
                try:
                    redis_client.set(KLINE_TASK_PROGRESS, progress_data, ex=3600)
                except Exception:
                    pass
            else:
                cache_set(KLINE_TASK_PROGRESS, progress_data, expire_seconds=3600)

        # 完成：更新 PG 记录
        progress_record.status = "completed"
        progress_record.completed = completed
        progress_record.failed = failed
        progress_record.finished_at = datetime.now()
        if errors:
            progress_record.error_detail = errors[:20]  # 最多保存20条错误
        db.commit()

        # 更新 Redis 最终状态
        final_data = json.dumps({
            "task_id": progress_record.id,
            "total": total,
            "completed": completed,
            "failed": failed,
            "status": "completed",
        })
        if redis_client:
            try:
                redis_client.set(KLINE_TASK_PROGRESS, final_data, ex=3600)
                redis_client.delete(KLINE_TASK_LOCK)
            except Exception:
                pass
        else:
            cache_set(KLINE_TASK_PROGRESS, final_data, expire_seconds=3600)
            from app.core.cache import cache_delete
            cache_delete(KLINE_TASK_LOCK)

        return {"status": "completed", "total": total, "completed": completed, "failed": failed}

    except Exception as e:
        db.rollback()
        logger.error(f"kline_batch_fetch fatal error: {e}")
        # 释放锁
        if redis_client:
            try:
                redis_client.delete(KLINE_TASK_LOCK)
            except Exception:
                pass
        else:
            from app.core.cache import cache_delete
            cache_delete(KLINE_TASK_LOCK)
        return {"status": "failed", "error": str(e)}
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

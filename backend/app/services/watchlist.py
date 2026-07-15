"""自选股管理服务，提供自选股的增删查和批量估值计算。

批量计算在 Celery 定时任务和 API 中复用，确保逻辑一致。
"""
from typing import Dict, List
from app.db.models import Watchlist, ValuationHistory
from app.services.valuation import ValuationService
from app.services.data_service import DataService


class WatchlistService:
    """自选股服务，管理自选股列表并触发估值计算。"""

    def __init__(self):
        self.valuation_service = ValuationService()
        self.data_service = DataService()

    def get_watchlist(self, db) -> List[Dict]:
        """查询全部自选股并返回其序列化信息列表。"""
        items = db.query(Watchlist).all()
        return [
            {
                "id": item.id,
                "stock_code": item.stock_code,
                "stock_name": item.stock_name,
                "industry": item.industry,
                "model_type": item.model_type,
                "ai_enabled": item.ai_enabled,
                "created_at": item.created_at,
                "updated_at": item.updated_at,
            }
            for item in items
        ]

    def add_stock(self, db, stock_code: str, stock_name: str, industry: str, model_type: str, ai_enabled: bool = False):
        """添加一只股票到自选股列表，重复添加会被拒绝。

        Args:
            db: 数据库会话。
            stock_code: 股票代码，唯一标识。
            stock_name: 股票名称。
            industry: 所属行业。
            model_type: 适用的估值模型代码。
            ai_enabled: 是否启用 AI 因子，默认 False。

        Returns:
            新增自选股的序列化字典。

        Raises:
            ValueError: 股票已存在于自选股列表时抛出。
        """
        existing = db.query(Watchlist).filter(Watchlist.stock_code == stock_code).first()
        if existing:
            raise ValueError(f"Stock {stock_code} already exists in watchlist")

        item = Watchlist(
            stock_code=stock_code,
            stock_name=stock_name,
            industry=industry,
            model_type=model_type,
            ai_enabled=ai_enabled,
        )
        db.add(item)
        db.commit()
        db.refresh(item)
        return {
            "id": item.id,
            "stock_code": item.stock_code,
            "stock_name": item.stock_name,
            "industry": item.industry,
            "model_type": item.model_type,
            "ai_enabled": item.ai_enabled,
        }

    def remove_stock(self, db, stock_code: str):
        """从自选股列表移除指定股票。

        Args:
            db: 数据库会话。
            stock_code: 待移除的股票代码。

        Returns:
            包含 stock_code 与 removed=True 的字典。

        Raises:
            ValueError: 股票不在自选股列表中时抛出。
        """
        item = db.query(Watchlist).filter(Watchlist.stock_code == stock_code).first()
        if not item:
            raise ValueError(f"Stock {stock_code} not found in watchlist")

        db.delete(item)
        db.commit()
        return {"stock_code": stock_code, "removed": True}

    def batch_calculate(self, db) -> List[Dict]:
        """批量计算自选股列表中所有股票的估值评分。

        为什么每次都写 DB：估值评分依赖历史趋势分析，DB 持久化支持
        后续回测与百分位计算，缺失历史数据会导致 percentile 失真。

        Args:
            db: 数据库会话。

        Returns:
            每只股票的计算结果列表，元素包含 stock_code、stock_name、
            score 与 status（success / no_data / error）。
        """
        items = db.query(Watchlist).all()
        results: List[Dict] = []

        for item in items:
            stock_code = item.stock_code
            stock_name = item.stock_name
            try:
                kline_data = self.data_service.get_kline_data(stock_code, db=db)
                if not kline_data:
                    results.append({
                        "stock_code": stock_code,
                        "stock_name": stock_name,
                        "score": None,
                        "status": "no_data",
                    })
                    continue

                stock_info = kline_data[0]
                historical = kline_data[1:]

                price = stock_info.get("price", 0)
                pe = stock_info.get("pe", 0)
                pb = stock_info.get("pb", 0)
                volume = stock_info.get("volume", 0)

                closes = [h["close"] for h in historical if h.get("close") is not None]
                ma20 = self.data_service.calculate_ma(stock_code, closes, period=20)
                ma60 = self.data_service.calculate_ma(stock_code, closes, period=60)
                volatility = self.data_service.calculate_volatility(stock_code, closes)

                volumes = [h["volume"] for h in historical if h.get("volume") is not None]
                if volumes:
                    avg_volume = sum(volumes) / len(volumes)
                    volume_ratio = volume / avg_volume if avg_volume else 1
                else:
                    volume_ratio = 1

                financial = self.data_service.get_financial_data(stock_code, db=db)

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

                result = self.valuation_service.calculate(
                    stock_code, item.model_type, data, ai_enabled=item.ai_enabled
                )

                factors = result.get("factors", {})
                score = result.get("score", 0)
                today = self.data_service.get_current_date()

                history = ValuationHistory(
                    stock_code=stock_code,
                    date=today,
                    score=score,
                    pe_score=factors.get("pe"),
                    pb_score=factors.get("pb"),
                    peg_score=factors.get("peg"),
                    ma_score=factors.get("ma_deviation"),
                    volatility_score=factors.get("volatility"),
                    volume_score=factors.get("volume"),
                    roe_score=factors.get("roe"),
                    dividend_score=factors.get("dividend"),
                    ai_score=factors.get("ai_analysis"),
                    pe=pe,
                    pb=pb,
                    price=price,
                )
                db.add(history)
                db.commit()

                results.append({
                    "stock_code": stock_code,
                    "stock_name": stock_name,
                    "score": score,
                    "status": "success",
                })

            except Exception as e:
                db.rollback()
                results.append({
                    "stock_code": stock_code,
                    "stock_name": stock_name,
                    "score": None,
                    "status": "error",
                    "error": str(e),
                })

        return results

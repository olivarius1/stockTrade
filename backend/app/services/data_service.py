"""数据服务模块，提供股票K线数据和财务数据的获取与计算。

为什么使用单独的 DataService 类而非直接在 API 中调用：
将数据获取逻辑与 API 路由解耦，便于在 Celery 定时任务和 API 中复用。

缓存策略说明：
- 实时行情和DB数据不缓存（保证数据一致性）
- 仅缓存计算量大的衍生数据（MA、波动率），用 len(prices) 作为数据版本标识
- K线数据更新时通过 cache_clear_pattern 清除衍生缓存
"""

import requests
import json
import logging
from typing import Dict, List
from datetime import date, timedelta, datetime
from app.db.models import KlineData, FinancialData
from app.core.cache import cache_get, cache_set, cache_clear_pattern

logger = logging.getLogger(__name__)


def _json_serializer(obj):
    """JSON 序列化辅助函数，处理 date/datetime 对象。

    为什么用 JSON 而非 eval：eval 不安全且无法处理日期对象，
    JSON 是标准序列化方式，通过 default 回调处理特殊类型。
    """
    if isinstance(obj, (date, datetime)):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")


def _json_deserializer(dct):
    """JSON 反序列化辅助函数，将 ISO 格式日期字符串还原为 date 对象。"""
    for key, val in dct.items():
        if isinstance(val, str):
            try:
                dct[key] = date.fromisoformat(val)
            except (ValueError, TypeError):
                pass
    return dct


class DataService:
    """股票数据服务，封装行情获取、历史数据查询和技术指标计算。"""

    def __init__(self):
        self.tencent_base_url = "https://qt.gtimg.cn"

    def get_kline_data(self, stock_code: str, start_date: date = None, end_date: date = None, db=None) -> List[Dict]:
        """获取股票K线数据，合并实时行情和历史数据。

        为什么不缓存：股票价格实时变动，缓存会导致估值基于过期价格。
        历史数据从DB查询，SQLAlchemy连接池已做优化，无需额外缓存。

        Args:
            stock_code: 股票代码，如 "600519"
            start_date: 开始日期，默认近10年
            end_date: 结束日期，默认今天
            db: 数据库会话

        Returns:
            列表，第一个元素是实时行情，后续是历史K线数据。
            失败时返回空列表。
        """
        if start_date is None:
            start_date = date.today() - timedelta(days=3650)
        if end_date is None:
            end_date = date.today()

        exchange = "sh" if stock_code.startswith("6") else "sz"
        url = f"{self.tencent_base_url}/q={exchange}{stock_code}"

        try:
            response = requests.get(url, timeout=10)
            data = response.text
            parts = data.split("~")

            stock_info = {
                "code": stock_code,
                "name": parts[1],
                "price": float(parts[3]),
                "open": float(parts[5]),
                "high": float(parts[4]),
                "low": float(parts[6]),
                "volume": int(parts[10]),
                "amount": float(parts[11]),
                "pe": float(parts[39]) if parts[39] else 0,
                "pb": float(parts[46]) if parts[46] else 0
            }

            historical_data = []
            if db:
                historical_data = db.query(KlineData).filter(
                    KlineData.stock_code == stock_code,
                    KlineData.date >= start_date,
                    KlineData.date <= end_date
                ).all()

            result = [stock_info]
            for row in historical_data:
                result.append({
                    "date": row.date,
                    "open": row.open,
                    "high": row.high,
                    "low": row.low,
                    "close": row.close,
                    "volume": row.volume,
                    "amount": row.amount
                })

            return result

        except Exception as e:
            logger.error(f"Failed to get kline data for {stock_code}: {e}")
            return []

    def get_financial_data(self, stock_code: str, db=None) -> Dict:
        """获取最新财务数据。

        为什么不缓存：财务数据更新频率用户可配置，缓存可能导致决策基于过期数据。
        SQLAlchemy连接池已优化DB查询，单用户场景QPS极低。

        Args:
            stock_code: 股票代码
            db: 数据库会话

        Returns:
            包含 eps, revenue, net_profit, roe, gross_margin, dividend_rate 的字典。
            无数据时返回空字典。
        """
        if db:
            latest = db.query(FinancialData).filter(
                FinancialData.stock_code == stock_code
            ).order_by(FinancialData.report_date.desc()).first()

            if latest:
                return {
                    "eps": latest.eps,
                    "revenue": latest.revenue,
                    "net_profit": latest.net_profit,
                    "roe": latest.roe,
                    "gross_margin": latest.gross_margin,
                    "dividend_rate": latest.dividend_rate
                }

        return {}

    def search_stock(self, keyword: str) -> List[Dict]:
        """搜索股票（当前为占位实现，后续接入搜索API）。"""
        return []

    def calculate_ma(self, stock_code: str, prices: List[float], period: int = 20) -> float:
        """计算移动平均线。

        为什么缓存：MA计算需要遍历价格序列，批量计算47只股票时开销显著。
        K线数据是append-only的，用 len(prices) 作为数据版本标识，
        数据不变时结果恒定，数据新增时长度变化自动失效缓存。

        Args:
            stock_code: 股票代码，用于缓存键
            prices: 收盘价列表
            period: 均线周期，默认20日

        Returns:
            移动平均值。数据不足时返回0。
        """
        if len(prices) < period:
            return 0

        cache_key = f"calc:ma:{stock_code}:{period}:{len(prices)}"
        cached = cache_get(cache_key)
        if cached is not None:
            try:
                return float(cached)
            except (ValueError, TypeError):
                pass

        result = sum(prices[-period:]) / period
        cache_set(cache_key, str(result), 3600)
        return result

    def calculate_volatility(self, stock_code: str, prices: List[float]) -> float:
        """计算价格波动率（日收益率标准差）。

        为什么缓存：波动率计算需要遍历全部价格序列两次，计算量大于MA。
        同理用 len(prices) 作为数据版本标识。

        Args:
            stock_code: 股票代码，用于缓存键
            prices: 收盘价列表

        Returns:
            波动率。数据不足时返回0。
        """
        if len(prices) < 2:
            return 0

        cache_key = f"calc:volatility:{stock_code}:{len(prices)}"
        cached = cache_get(cache_key)
        if cached is not None:
            try:
                return float(cached)
            except (ValueError, TypeError):
                pass

        returns = []
        for i in range(1, len(prices)):
            returns.append((prices[i] - prices[i-1]) / prices[i-1])
        if not returns:
            return 0
        mean = sum(returns) / len(returns)
        variance = sum((r - mean) ** 2 for r in returns) / len(returns)
        result = variance ** 0.5

        cache_set(cache_key, str(result), 3600)
        return result

    def get_current_date(self) -> date:
        """返回当前日期，用于估值评分记录。"""
        return date.today()

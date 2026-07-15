import requests
from typing import Dict, List
from datetime import date, timedelta
from app.db.models import KlineData, FinancialData
from app.core.cache import cache_get, cache_set

class DataService:
    def __init__(self):
        self.tencent_base_url = "https://qt.gtimg.cn"
    
    def get_kline_data(self, stock_code: str, start_date: date = None, end_date: date = None, db=None) -> List[Dict]:
        if start_date is None:
            start_date = date.today() - timedelta(days=3650)
        if end_date is None:
            end_date = date.today()
        
        cached = cache_get(f"kline:{stock_code}:{start_date}:{end_date}")
        if cached:
            return eval(cached)
        
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
            
            cache_set(f"kline:{stock_code}:{start_date}:{end_date}", str(result), 3600)
            return result
        
        except Exception as e:
            return []
    
    def get_financial_data(self, stock_code: str, db=None) -> Dict:
        cached = cache_get(f"financial:{stock_code}")
        if cached:
            return eval(cached)
        
        if db:
            latest = db.query(FinancialData).filter(
                FinancialData.stock_code == stock_code
            ).order_by(FinancialData.report_date.desc()).first()
            
            if latest:
                result = {
                    "eps": latest.eps,
                    "revenue": latest.revenue,
                    "net_profit": latest.net_profit,
                    "roe": latest.roe,
                    "gross_margin": latest.gross_margin,
                    "dividend_rate": latest.dividend_rate
                }
                cache_set(f"financial:{stock_code}", str(result), 7 * 24 * 3600)
                return result
        
        return {}
    
    def search_stock(self, keyword: str) -> List[Dict]:
        return []
    
    def calculate_ma(self, prices: List[float], period: int = 20) -> float:
        if len(prices) < period:
            return 0
        return sum(prices[-period:]) / period
    
    def calculate_volatility(self, prices: List[float]) -> float:
        if len(prices) < 2:
            return 0
        returns = []
        for i in range(1, len(prices)):
            returns.append((prices[i] - prices[i-1]) / prices[i-1])
        if not returns:
            return 0
        mean = sum(returns) / len(returns)
        variance = sum((r - mean) ** 2 for r in returns) / len(returns)
        return variance ** 0.5
    
    def get_current_date(self) -> date:
        return date.today()

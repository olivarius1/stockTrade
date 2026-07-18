from app.plugins.factors.base import ValuationFactor, register_factor
from typing import List, Dict

@register_factor
class RevenueGrowth5YFactor(ValuationFactor):
    def get_name(self) -> str:
        return "5年营收增长率评分"
    
    def get_code(self) -> str:
        return "revenue_growth_5y"
    
    def requires_data(self) -> List[str]:
        return ["financial"]
    
    def score(self, data: Dict) -> float:
        """
        5年营收增长率评分：越高越好
        data 中需包含:
          - revenue_growth_5y: 5年营收复合增长率（小数形式，如0.15表示15%）
        """
        g = data.get("revenue_growth_5y", 0)
        if g <= 0:
            return 25
        elif g >= 0.25:
            return 95
        elif g >= 0.20:
            return 85
        elif g >= 0.15:
            return 75
        elif g >= 0.10:
            return 60
        elif g >= 0.05:
            return 45
        else:
            return 30

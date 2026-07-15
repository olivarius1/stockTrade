from app.plugins.factors.base import ValuationFactor, register_factor
from typing import List, Dict

@register_factor
class VolatilityFactor(ValuationFactor):
    def get_name(self) -> str:
        return "波动率"
    
    def get_code(self) -> str:
        return "volatility"
    
    def requires_data(self) -> List[str]:
        return ["kline"]
    
    def score(self, data: Dict) -> float:
        volatility = data.get("volatility", 0)
        
        if volatility <= 0.02:
            return 85
        elif volatility <= 0.04:
            return 70
        elif volatility <= 0.06:
            return 55
        elif volatility <= 0.08:
            return 40
        elif volatility <= 0.10:
            return 25
        else:
            return 20

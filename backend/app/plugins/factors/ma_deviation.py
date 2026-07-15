from app.plugins.factors.base import ValuationFactor, register_factor
from typing import List, Dict

@register_factor
class MADeviationFactor(ValuationFactor):
    def get_name(self) -> str:
        return "MA偏离度"
    
    def get_code(self) -> str:
        return "ma_deviation"
    
    def requires_data(self) -> List[str]:
        return ["kline"]
    
    def score(self, data: Dict) -> float:
        price = data.get("price", 0)
        ma20 = data.get("ma20", 0)
        ma60 = data.get("ma60", 0)
        
        if ma60 == 0:
            return 50
        
        deviation = (price - ma60) / ma60
        
        if deviation <= -0.2:
            return 95
        elif deviation <= -0.1:
            return 80
        elif deviation <= -0.05:
            return 65
        elif deviation <= 0.05:
            return 50
        elif deviation <= 0.1:
            return 35
        else:
            return 20

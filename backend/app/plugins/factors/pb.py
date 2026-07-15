from app.plugins.factors.base import ValuationFactor, register_factor
from typing import List, Dict

@register_factor
class PBFactor(ValuationFactor):
    def get_name(self) -> str:
        return "PB评分"
    
    def get_code(self) -> str:
        return "pb"
    
    def requires_data(self) -> List[str]:
        return ["kline", "pb_range"]
    
    def score(self, data: Dict) -> float:
        pb = data.get("pb", 0)
        pb_min = data.get("pb_min", 0.5)
        pb_max = data.get("pb_max", 10)
        
        if pb <= pb_min:
            return 95
        elif pb <= pb_min * 1.5:
            return 80
        elif pb <= pb_min * 2:
            return 65
        elif pb <= pb_max * 0.7:
            return 50
        elif pb <= pb_max:
            return 35
        else:
            return 20

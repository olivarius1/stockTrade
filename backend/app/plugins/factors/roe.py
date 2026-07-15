from app.plugins.factors.base import ValuationFactor, register_factor
from typing import List, Dict

@register_factor
class ROEFactor(ValuationFactor):
    def get_name(self) -> str:
        return "ROE评分"
    
    def get_code(self) -> str:
        return "roe"
    
    def requires_data(self) -> List[str]:
        return ["financial"]
    
    def score(self, data: Dict) -> float:
        roe = data.get("roe", 0)
        roe_min = data.get("roe_min", 0.05)
        roe_max = data.get("roe_max", 0.20)
        
        if roe >= roe_max:
            return 95
        elif roe >= roe_max * 0.8:
            return 80
        elif roe >= roe_max * 0.6:
            return 65
        elif roe >= roe_min * 1.5:
            return 50
        elif roe >= roe_min:
            return 35
        else:
            return 20

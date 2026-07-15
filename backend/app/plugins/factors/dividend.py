from app.plugins.factors.base import ValuationFactor, register_factor
from typing import List, Dict

@register_factor
class DividendFactor(ValuationFactor):
    def get_name(self) -> str:
        return "股息率"
    
    def get_code(self) -> str:
        return "dividend"
    
    def requires_data(self) -> List[str]:
        return ["financial"]
    
    def score(self, data: Dict) -> float:
        dividend_rate = data.get("dividend_rate", 0)
        div_min = data.get("dividend_min", 0.02)
        div_max = data.get("dividend_max", 0.10)
        
        if dividend_rate >= div_max:
            return 95
        elif dividend_rate >= div_max * 0.8:
            return 80
        elif dividend_rate >= div_max * 0.6:
            return 65
        elif dividend_rate >= div_min * 1.5:
            return 50
        elif dividend_rate >= div_min:
            return 35
        else:
            return 20

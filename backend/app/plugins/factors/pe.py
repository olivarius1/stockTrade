from app.plugins.factors.base import ValuationFactor, register_factor
from typing import List, Dict

@register_factor
class PEFactor(ValuationFactor):
    def get_name(self) -> str:
        return "PE评分"
    
    def get_code(self) -> str:
        return "pe"
    
    def requires_data(self) -> List[str]:
        return ["kline", "pe_range"]
    
    def score(self, data: Dict) -> float:
        pe = data.get("pe", 0)
        pe_min = data.get("pe_min", 5)
        pe_max = data.get("pe_max", 50)
        
        if pe <= pe_min:
            return 95
        elif pe <= pe_min * 1.5:
            return 80
        elif pe <= pe_min * 2:
            return 65
        elif pe <= pe_max * 0.7:
            return 50
        elif pe <= pe_max:
            return 35
        else:
            return 20

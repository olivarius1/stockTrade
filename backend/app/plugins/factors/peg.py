from app.plugins.factors.base import ValuationFactor, register_factor
from typing import List, Dict

@register_factor
class PEGFactor(ValuationFactor):
    def get_name(self) -> str:
        return "PEG评分"
    
    def get_code(self) -> str:
        return "peg"
    
    def requires_data(self) -> List[str]:
        return ["kline", "eps_growth"]
    
    def score(self, data: Dict) -> float:
        pe = data.get("pe", 0)
        eps_growth = data.get("eps_growth", 0.1)
        
        if eps_growth <= 0:
            return 20
        
        peg = pe / (eps_growth * 100)
        
        if peg <= 0.5:
            return 95
        elif peg <= 1.0:
            return 80
        elif peg <= 1.2:
            return 65
        elif peg <= 1.5:
            return 50
        elif peg <= 2.0:
            return 35
        else:
            return 20

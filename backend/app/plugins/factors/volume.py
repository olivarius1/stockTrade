from app.plugins.factors.base import ValuationFactor, register_factor
from typing import List, Dict

@register_factor
class VolumeFactor(ValuationFactor):
    def get_name(self) -> str:
        return "量能"
    
    def get_code(self) -> str:
        return "volume"
    
    def requires_data(self) -> List[str]:
        return ["kline"]
    
    def score(self, data: Dict) -> float:
        volume_ratio = data.get("volume_ratio", 1)
        
        if volume_ratio >= 2.0:
            return 90
        elif volume_ratio >= 1.5:
            return 75
        elif volume_ratio >= 1.0:
            return 60
        elif volume_ratio >= 0.7:
            return 45
        elif volume_ratio >= 0.5:
            return 30
        else:
            return 20

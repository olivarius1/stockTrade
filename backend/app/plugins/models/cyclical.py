from app.plugins.models.base import ValuationModel, register_model
from typing import List, Dict

@register_model
class CyclicalModel(ValuationModel):
    def get_name(self) -> str:
        return "周期股"
    
    def get_code(self) -> str:
        return "cyclical"
    
    def get_factors(self) -> List[str]:
        return ["pe", "pb", "ma_deviation", "volatility", "volume"]
    
    def get_weights(self) -> Dict[str, float]:
        return {
            "pe": 0.30,
            "pb": 0.20,
            "ma_deviation": 0.20,
            "volatility": 0.15,
            "volume": 0.15
        }
    
    def get_params(self) -> Dict[str, float]:
        return {
            "pe_min": 3,
            "pe_max": 30,
            "pb_min": 0.5,
            "pb_max": 5,
            "eps_growth": 0.10
        }

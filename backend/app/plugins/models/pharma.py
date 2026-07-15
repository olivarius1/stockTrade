from app.plugins.models.base import ValuationModel, register_model
from typing import List, Dict

@register_model
class PharmaModel(ValuationModel):
    def get_name(self) -> str:
        return "医药股"
    
    def get_code(self) -> str:
        return "pharma"
    
    def get_factors(self) -> List[str]:
        return ["peg", "pe", "pb", "ma_deviation", "volatility", "volume"]
    
    def get_weights(self) -> Dict[str, float]:
        return {
            "peg": 0.30,
            "pe": 0.25,
            "pb": 0.15,
            "ma_deviation": 0.15,
            "volatility": 0.10,
            "volume": 0.05
        }
    
    def get_params(self) -> Dict[str, float]:
        return {
            "pe_min": 15,
            "pe_max": 60,
            "pb_min": 3,
            "pb_max": 15,
            "eps_growth": 0.18
        }

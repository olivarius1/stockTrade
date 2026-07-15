from app.plugins.models.base import ValuationModel, register_model
from typing import List, Dict

@register_model
class TechModel(ValuationModel):
    def get_name(self) -> str:
        return "科技股"
    
    def get_code(self) -> str:
        return "tech"
    
    def get_factors(self) -> List[str]:
        return ["peg", "pe", "pb", "ma_deviation", "volatility", "volume"]
    
    def get_weights(self) -> Dict[str, float]:
        return {
            "peg": 0.30,
            "pe": 0.24,
            "pb": 0.14,
            "ma_deviation": 0.18,
            "volatility": 0.12,
            "volume": 0.02
        }
    
    def get_params(self) -> Dict[str, float]:
        return {
            "pe_min": 10,
            "pe_max": 80,
            "pb_min": 2,
            "pb_max": 20,
            "eps_growth": 0.20
        }

from app.plugins.models.base import ValuationModel, register_model
from typing import List, Dict

@register_model
class SOEModel(ValuationModel):
    def get_name(self) -> str:
        return "央企国企"
    
    def get_code(self) -> str:
        return "soe"
    
    def get_factors(self) -> List[str]:
        return ["pb", "roe", "dividend", "ma_deviation", "volatility", "volume"]
    
    def get_weights(self) -> Dict[str, float]:
        return {
            "pb": 0.25,
            "roe": 0.20,
            "dividend": 0.20,
            "ma_deviation": 0.15,
            "volatility": 0.10,
            "volume": 0.10
        }
    
    def get_params(self) -> Dict[str, float]:
        return {
            "pb_min": 0.8,
            "pb_max": 3,
            "roe_min": 0.06,
            "roe_max": 0.15,
            "dividend_min": 0.03,
            "dividend_max": 0.08
        }

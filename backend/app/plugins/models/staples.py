from app.plugins.models.base import ValuationModel, register_model
from typing import List, Dict

@register_model
class StaplesModel(ValuationModel):
    def get_name(self) -> str:
        return "必选消费"
    
    def get_code(self) -> str:
        return "staples"
    
    def get_factors(self) -> List[str]:
        return ["pe", "peg", "pb", "ma_deviation", "volatility", "volume"]
    
    def get_weights(self) -> Dict[str, float]:
        return {
            "pe": 0.31,
            "peg": 0.22,
            "pb": 0.13,
            "ma_deviation": 0.13,
            "volatility": 0.11,
            "volume": 0.09
        }
    
    def get_params(self) -> Dict[str, float]:
        return {
            "pe_min": 5,
            "pe_max": 40,
            "pb_min": 1,
            "pb_max": 10,
            "eps_growth": 0.15
        }

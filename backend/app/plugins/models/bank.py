from app.plugins.models.base import ValuationModel, register_model
from typing import List, Dict

@register_model
class BankModel(ValuationModel):
    def get_name(self) -> str:
        return "银行保险"
    
    def get_code(self) -> str:
        return "bank"
    
    def get_factors(self) -> List[str]:
        return ["pb", "roe", "dividend", "ma_deviation", "volatility"]
    
    def get_weights(self) -> Dict[str, float]:
        return {
            "pb": 0.30,
            "roe": 0.25,
            "dividend": 0.15,
            "ma_deviation": 0.15,
            "volatility": 0.15
        }
    
    def get_params(self) -> Dict[str, float]:
        return {
            "pb_min": 0.5,
            "pb_max": 2,
            "roe_min": 0.05,
            "roe_max": 0.20,
            "dividend_min": 0.02,
            "dividend_max": 0.10
        }

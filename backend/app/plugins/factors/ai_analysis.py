from app.plugins.factors.base import ValuationFactor, register_factor
from typing import List, Dict

@register_factor
class AIAnalysisFactor(ValuationFactor):
    def get_name(self) -> str:
        return "AI深度分析"
    
    def get_code(self) -> str:
        return "ai_analysis"
    
    def requires_data(self) -> List[str]:
        return ["financial", "market"]
    
    def score(self, data: Dict) -> float:
        ai_score = data.get("ai_score", 50)
        return ai_score

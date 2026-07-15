from typing import Dict, List, Optional
from app.plugins.models.base import get_model, list_models
from app.plugins.factors.base import get_factor, list_factors
from app.db.models import ValuationHistory

class ValuationService:
    def __init__(self):
        pass
    
    def calculate(self, stock_code: str, model_code: str, data: Dict, ai_enabled: bool = False) -> Dict:
        model = get_model(model_code)
        if not model:
            raise ValueError(f"Model {model_code} not found")
        
        model_instance = model()
        factors = model_instance.get_factors()
        weights = model_instance.get_weights()
        params = model_instance.get_params()
        
        if ai_enabled:
            factors.append("ai_analysis")
            weights["ai_analysis"] = 0.10
        
        total_weight = sum(weights.values())
        normalized_weights = {k: v / total_weight for k, v in weights.items()}
        
        factor_scores = {}
        total_score = 0.0
        
        for factor_code in factors:
            factor = get_factor(factor_code)
            if not factor:
                continue
            
            factor_data = {**data, **params}
            factor_instance = factor()
            score = factor_instance.score(factor_data)
            factor_scores[factor_code] = score
            total_score += score * normalized_weights.get(factor_code, 0)
        
        result = {
            "stock_code": stock_code,
            "score": round(total_score, 2),
            "factors": factor_scores,
            "weights": normalized_weights,
            "params": params
        }
        return result
    
    def calculate_percentile(self, stock_code: str, score: float, db) -> float:
        history = db.query(ValuationHistory).filter(
            ValuationHistory.stock_code == stock_code
        ).all()
        
        if not history:
            return 50.0
        
        scores = [h.score for h in history]
        scores.append(score)
        scores.sort()
        
        rank = scores.index(score)
        percentile = (rank / len(scores)) * 100
        return round(percentile, 2)
    
    def get_status(self, percentile: float) -> str:
        if percentile >= 90:
            return "极度低估"
        elif percentile >= 70:
            return "低估"
        elif percentile >= 50:
            return "中性偏低"
        elif percentile >= 30:
            return "中性偏高"
        elif percentile >= 10:
            return "高估"
        else:
            return "极度高估"
    
    def get_models(self) -> List[Dict]:
        return list_models()
    
    def get_factors(self) -> List[Dict]:
        return list_factors()

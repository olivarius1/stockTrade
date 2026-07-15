"""估值计算服务，协调估值模型和因子插件计算股票估值评分。

为什么用插件化设计：不同行业股票适用不同估值模型（如银行用PB，科技股用PE），
插件化允许灵活添加新模型和因子，无需修改核心逻辑。
"""
from typing import Dict, List, Optional
from app.plugins.models.base import get_model, list_models
from app.plugins.factors.base import get_factor, list_factors
from app.db.models import ValuationHistory

class ValuationService:
    """估值服务，通过模型插件和因子插件计算综合估值评分。"""

    def __init__(self):
        pass

    def calculate(self, stock_code: str, model_code: str, data: Dict, ai_enabled: bool = False) -> Dict:
        """计算单只股票的综合估值评分。

        流程：加载估值模型插件 → 获取因子列表与权重 → 逐个调用因子插件
        计算分项得分 → 按归一化权重加权汇总为总分。AI 因子可选，启用时
        占 10% 权重并将其他因子权重重新归一化，以保持总和为 1。

        Args:
            stock_code: 股票代码。
            model_code: 估值模型代码，用于定位模型插件。
            data: 原始指标数据（行情、财务等），传给各因子插件。
            ai_enabled: 是否启用 AI 分析因子，默认 False。

        Returns:
            包含 stock_code、score（加权总分）、factors（各因子得分）、
            weights（归一化权重）、params（模型参数）的字典。

        Raises:
            ValueError: 指定的 model_code 找不到对应模型插件时抛出。
        """
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
        """计算当前评分在历史评分序列中的百分位。

        百分位越高表示当前估值越低（更便宜）；无历史数据时返回 50.0
        作为中性默认值，避免新上市股票因缺乏历史而判定异常。

        Args:
            stock_code: 股票代码，用于查询历史评分。
            score: 当前估值评分。
            db: 数据库会话。

        Returns:
            0~100 之间的百分位数值，保留两位小数。
        """
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
        """根据百分位返回中文估值状态描述。

        百分位越高代表越低估（更具投资价值），越低代表越高估。

        Args:
            percentile: 0~100 之间的百分位数值。

        Returns:
            估值状态字符串，如 "极度低估"、"低估"、"中性偏低"、
            "中性偏高"、"高估"、"极度高估"。
        """
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
        """返回所有已注册的估值模型元信息列表。"""
        return list_models()

    def get_factors(self) -> List[Dict]:
        """返回所有已注册的因子插件元信息列表。"""
        return list_factors()

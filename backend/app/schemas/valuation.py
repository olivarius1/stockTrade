from pydantic import BaseModel
from datetime import date
from typing import Optional, Dict, List

class ScoreBands(BaseModel):
    """估值分五档分级阈值，基于个股或同模型历史分布计算。"""
    thresholds: Dict[str, float]  # {"p10": x, "p25": x, "p50": x, "p75": x, "p90": x}
    source: str       # "stock" = 个股数据, "model" = 同模型合并
    sample_count: int  # 样本量
    band_label: str    # 当前分数所处档位，如 "中性"、"极高(低估)"

class ValuationFactor(BaseModel):
    code: str
    name: str
    score: float
    weight: float

class ValuationResult(BaseModel):
    stock_code: str
    stock_name: str
    date: date
    score: float
    percentile: float
    status: str
    pe: float
    pb: float
    price: float
    factors: Dict[str, float]
    score_bands: Optional[ScoreBands] = None

class ValuationHistoryItem(BaseModel):
    date: date
    score: float
    price: float
    pe: Optional[float]
    pb: Optional[float]
    pe_score: Optional[float]
    pb_score: Optional[float]
    peg_score: Optional[float]
    ma_score: Optional[float]
    volatility_score: Optional[float]
    volume_score: Optional[float]
    roe_score: Optional[float]
    dividend_score: Optional[float]
    ai_score: Optional[float]

class MarketUndervaluedItem(BaseModel):
    """全市场低估股票条目。"""
    stock_code: str
    stock_name: str
    score: float
    percentile: float
    status: str
    industry: Optional[str] = ""
    model_type: Optional[str] = ""
    price: Optional[float] = None
    valuation_date: Optional[date] = None
    is_latest: bool = True

class SectorInfo(BaseModel):
    """板块信息。"""
    industry: str
    count: int

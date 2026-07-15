from pydantic import BaseModel
from datetime import date
from typing import Optional, Dict

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

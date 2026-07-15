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

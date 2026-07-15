from pydantic import BaseModel
from datetime import date

class StockInfo(BaseModel):
    code: str
    name: str
    industry: str
    pe: float
    pb: float
    price: float

class KlineData(BaseModel):
    date: date
    open: float
    high: float
    low: float
    close: float
    volume: int
    amount: float

class StockSearchResponse(BaseModel):
    code: str
    name: str

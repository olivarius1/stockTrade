from pydantic import BaseModel
from datetime import datetime

class WatchlistItem(BaseModel):
    stock_code: str
    stock_name: str
    industry: str
    model_type: str
    ai_enabled: bool = False

class WatchlistResponse(BaseModel):
    id: int
    stock_code: str
    stock_name: str
    industry: str
    model_type: str
    ai_enabled: bool
    created_at: datetime

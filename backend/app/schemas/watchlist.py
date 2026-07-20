from pydantic import BaseModel
from datetime import datetime, date
from typing import Optional

class WatchlistItem(BaseModel):
    stock_code: str
    stock_name: Optional[str] = ""
    industry: Optional[str] = ""
    model_type: str
    ai_enabled: bool = False
    group_id: Optional[int] = None

class WatchlistResponse(BaseModel):
    id: int
    stock_code: str
    stock_name: str
    industry: str
    model_type: str
    ai_enabled: bool
    group_id: Optional[int] = None
    created_at: datetime

class WatchlistSummaryItem(BaseModel):
    """自选股估值摘要，首页列表核心数据结构。"""
    stock_code: str
    stock_name: str
    model_type: str
    industry: Optional[str] = ""
    group_id: Optional[int] = None
    score: Optional[float] = None
    percentile: Optional[float] = None
    status: Optional[str] = None
    valuation_date: Optional[date] = None
    is_latest: bool = True

class StockGroupCreate(BaseModel):
    name: str
    sort_order: int = 0

class StockGroupResponse(BaseModel):
    id: int
    name: str
    sort_order: int
    stock_count: int = 0

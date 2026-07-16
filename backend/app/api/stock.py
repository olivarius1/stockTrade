"""股票数据API，提供股票搜索、基本信息查询和估值历史。"""
from datetime import date
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, select

from app.db.session import get_db
from app.db.models import ValuationHistory
from app.services.data_service import DataService
from app.services.valuation import ValuationService
from app.schemas.stock import StockInfo, StockSearchResponse
from app.schemas.valuation import ValuationResult, ValuationHistoryItem

router = APIRouter()


@router.get("/search", response_model=List[StockSearchResponse])
def search_stocks(keyword: str = Query(..., description="搜索关键词")):
    """搜索股票（当前为占位实现）。"""
    data_service = DataService()
    results = data_service.search_stock(keyword)
    return results


@router.get("/{code}", response_model=StockInfo)
def get_stock_info(code: str, db: Session = Depends(get_db)):
    """获取股票基本信息（名称、PE、PB、当前价格）。"""
    data_service = DataService()
    kline_data = data_service.get_kline_data(code, db=db)
    if not kline_data:
        raise HTTPException(status_code=404, detail="Stock not found")
    info = kline_data[0]
    return StockInfo(
        code=info.get("code", code),
        name=info.get("name", ""),
        industry="",
        pe=info.get("pe", 0),
        pb=info.get("pb", 0),
        price=info.get("price", 0),
    )


@router.get("/{code}/valuation", response_model=ValuationResult)
def get_valuation(
    code: str,
    model_code: str = Query("tech", description="估值模型代码"),
    db: Session = Depends(get_db),
):
    """计算并返回股票估值报告（兼容旧接口，推荐使用 /api/valuation/report/{code}）。"""
    data_service = DataService()
    valuation_service = ValuationService()

    kline_data = data_service.get_kline_data(code, db=db)
    if not kline_data:
        raise HTTPException(status_code=404, detail="Stock not found")

    current = kline_data[0]
    historical = kline_data[1:]

    prices = [item["close"] for item in historical if "close" in item]
    ma20 = data_service.calculate_ma(code, prices, period=20)
    ma60 = data_service.calculate_ma(code, prices, period=60)
    volatility = data_service.calculate_volatility(code, prices)

    financial = data_service.get_financial_data(code, db=db)

    data = {
        "code": current.get("code", code),
        "name": current.get("name", ""),
        "price": current.get("price", 0),
        "pe": current.get("pe", 0),
        "pb": current.get("pb", 0),
        "volume": current.get("volume", 0),
        "ma20": ma20,
        "ma60": ma60,
        "volatility": volatility,
        **financial,
    }

    try:
        result = valuation_service.calculate(code, model_code, data, ai_enabled=False)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    percentile = valuation_service.calculate_percentile(code, result["score"], db)
    status_text = valuation_service.get_status(percentile)

    return ValuationResult(
        stock_code=code,
        stock_name=current.get("name", ""),
        date=data_service.get_current_date(),
        score=result["score"],
        percentile=percentile,
        status=status_text,
        pe=current.get("pe", 0),
        pb=current.get("pb", 0),
        price=current.get("price", 0),
        factors=result["factors"],
    )


@router.get("/{code}/history", response_model=List[ValuationHistoryItem])
def get_valuation_history(
    code: str,
    start_date: date = Query(None),
    end_date: date = Query(None),
    db: Session = Depends(get_db),
):
    """获取股票估值评分历史（兼容旧接口，推荐使用 /api/valuation/history/{code}）。

    同一天取 id 最大的一条，避免多任务并发写入导致图表数据点重复。
    """
    subq = db.query(
        func.max(ValuationHistory.id).label("max_id")
    ).filter(
        ValuationHistory.stock_code == code
    )
    if start_date:
        subq = subq.filter(ValuationHistory.date >= start_date)
    if end_date:
        subq = subq.filter(ValuationHistory.date <= end_date)
    subq = subq.group_by(ValuationHistory.date).subquery()

    history = db.query(ValuationHistory).filter(
        ValuationHistory.id.in_(select(subq.c.max_id))
    ).order_by(ValuationHistory.date).all()
    return [
        ValuationHistoryItem(date=h.date, score=h.score, price=h.price)
        for h in history
    ]

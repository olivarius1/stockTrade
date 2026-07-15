"""估值API，提供估值报告和估值历史查询。

为什么独立路由模块：估值是系统核心功能，独立路由使URL语义更清晰
（/api/valuation/report/{code} 比 /api/stock/{code}/valuation 更直观）。
"""
from datetime import date
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models import ValuationHistory
from app.services.data_service import DataService
from app.services.valuation import ValuationService
from app.schemas.valuation import ValuationResult, ValuationHistoryItem

router = APIRouter()


@router.get("/report/{code}", response_model=ValuationResult)
def get_valuation_report(
    code: str,
    model_code: str = Query("tech", description="估值模型代码"),
    db: Session = Depends(get_db),
):
    """获取股票估值报告，包含综合评分、百分位、因子得分详情。"""
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


@router.get("/history/{code}", response_model=List[ValuationHistoryItem])
def get_valuation_history(
    code: str,
    start_date: date = Query(None),
    end_date: date = Query(None),
    db: Session = Depends(get_db),
):
    """获取股票估值评分历史，用于绘制估值趋势曲线。"""
    query = db.query(ValuationHistory).filter(ValuationHistory.stock_code == code)
    if start_date:
        query = query.filter(ValuationHistory.date >= start_date)
    if end_date:
        query = query.filter(ValuationHistory.date <= end_date)
    history = query.order_by(ValuationHistory.date).all()
    return [
        ValuationHistoryItem(date=h.date, score=h.score, price=h.price)
        for h in history
    ]

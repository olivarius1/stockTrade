"""估值API，提供估值报告和估值历史查询。

为什么独立路由模块：估值是系统核心功能，独立路由使URL语义更清晰
（/api/valuation/report/{code} 比 /api/stock/{code}/valuation 更直观）。
"""
from datetime import date
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, select

from app.db.session import get_db
from app.db.models import ValuationHistory, Watchlist
from app.services.data_service import DataService
from app.services.valuation import ValuationService
from app.schemas.valuation import ValuationResult, ValuationHistoryItem, ScoreBands, MarketUndervaluedItem

router = APIRouter()


@router.post("/incremental/{code}")
def incremental_calculate(
    code: str,
    db: Session = Depends(get_db),
):
    """增量计算：查看K线范围，补齐缺失的估值历史（早期+近期）。"""
    # 获取股票的模型配置
    wl = db.query(Watchlist).filter(Watchlist.stock_code == code).first()
    model_type = wl.model_type if wl else "tech"
    ai_enabled = wl.ai_enabled if wl else False

    from app.services.watchlist import WatchlistService
    service = WatchlistService()
    result = service.incremental_calculate(db, code, model_type, ai_enabled)
    return result


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

    # 计算五档分级
    bands_data = valuation_service.get_score_bands(code, model_code, db)
    score_bands = None
    if bands_data:
        band_label = valuation_service.get_band_label(result["score"], bands_data)
        score_bands = ScoreBands(
            thresholds=bands_data["thresholds"],
            source=bands_data["source"],
            sample_count=bands_data["sample_count"],
            band_label=band_label,
        )

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
        score_bands=score_bands,
    )


@router.get("/history/{code}", response_model=List[ValuationHistoryItem])
def get_valuation_history(
    code: str,
    start_date: date = Query(None),
    end_date: date = Query(None),
    db: Session = Depends(get_db),
):
    """获取股票估值评分历史，包含各因子得分，用于绘制估值趋势曲线和联动对比。

    同一天可能存在多条记录（多任务并发写入或手动重算），这里按日期取
    id 最大的一条（最后写入的），确保图表上每天只有一个数据点。
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
        ValuationHistoryItem(
            date=h.date,
            score=h.score,
            price=h.price,
            pe=h.pe,
            pb=h.pb,
            pe_score=h.pe_score,
            pb_score=h.pb_score,
            peg_score=h.peg_score,
            ma_score=h.ma_score,
            volatility_score=h.volatility_score,
            volume_score=h.volume_score,
            roe_score=h.roe_score,
            dividend_score=h.dividend_score,
            ai_score=h.ai_score,
        )
        for h in history
    ]


@router.get("/market/undervalued", response_model=List[MarketUndervaluedItem])
def get_market_undervalued(
    limit: int = Query(50, ge=1, le=200),
    industry: str = Query(None),
    model_type: str = Query(None),
    db: Session = Depends(get_db),
):
    """全市场低估排行，按估值分降序返回 Top N。"""
    # 全局最新交易日
    latest_date = db.query(func.max(ValuationHistory.date)).scalar()
    if not latest_date:
        return []

    # 每只股票最新估值记录
    latest_subq = db.query(
        ValuationHistory.stock_code,
        func.max(ValuationHistory.id).label("max_id")
    ).group_by(ValuationHistory.stock_code).subquery()

    # 查询最新估值记录，按分数降序
    query = db.query(ValuationHistory).filter(
        ValuationHistory.id.in_(select(latest_subq.c.max_id))
    ).order_by(ValuationHistory.score.desc())

    valuations = query.limit(limit * 2).all()  # 多取一些以便筛选后仍有足够数据

    # 关联 Watchlist 获取名称/行业/模型
    stock_codes = [v.stock_code for v in valuations]
    watchlist_map = {}
    if stock_codes:
        wl_items = db.query(Watchlist).filter(Watchlist.stock_code.in_(stock_codes)).all()
        watchlist_map = {w.stock_code: w for w in wl_items}

    valuation_service = ValuationService()
    result = []
    for val in valuations:
        wl = watchlist_map.get(val.stock_code)
        # 筛选
        if industry and (not wl or wl.industry != industry):
            continue
        if model_type and (not wl or wl.model_type != model_type):
            continue

        percentile = valuation_service.calculate_percentile(val.stock_code, val.score, db)
        status = valuation_service.get_status(percentile)

        result.append(MarketUndervaluedItem(
            stock_code=val.stock_code,
            stock_name=wl.stock_name if wl else val.stock_code,
            score=val.score,
            percentile=percentile,
            status=status,
            industry=wl.industry if wl else "",
            model_type=wl.model_type if wl else "",
            price=val.price,
            valuation_date=val.date,
            is_latest=(val.date == latest_date),
        ))
        if len(result) >= limit:
            break

    return result

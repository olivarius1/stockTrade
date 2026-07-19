"""自选股API，提供自选股管理和批量估值计算。"""
import re
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models import Watchlist
from app.services.data_service import DataService
from app.services.valuation import ValuationService
from app.schemas.watchlist import WatchlistItem, WatchlistResponse

router = APIRouter()


def normalize_stock_code(raw_code: str) -> str:
    """标准化股票代码，支持多种格式。

    支持: 000001、000001.sz、000001.SZ、sh.000001、SH.000001
    返回: 纯数字代码，如 000001
    """
    code = raw_code.strip().upper()
    # 格式: sh.000001 / sz.000001
    m = re.match(r'^(SH|SZ)\.(\d{6})$', code)
    if m:
        return m.group(2)
    # 格式: 000001.sh / 000001.sz
    m = re.match(r'^(\d{6})\.(SH|SZ)$', code)
    if m:
        return m.group(1)
    # 格式: 纯数字
    m = re.match(r'^(\d{6})$', code)
    if m:
        return m.group(1)
    return raw_code.strip()


def _batch_calculate(db: Session) -> dict:
    """批量计算自选股估值的内联实现（WatchlistService 不可用时的降级方案）。"""
    items = db.query(Watchlist).all()
    results = []
    data_service = DataService()
    valuation_service = ValuationService()

    for item in items:
        try:
            kline_data = data_service.get_kline_data(item.stock_code, db=db)
            if not kline_data:
                results.append({
                    "stock_code": item.stock_code,
                    "stock_name": item.stock_name,
                    "error": "No data",
                })
                continue

            current = kline_data[0]
            historical = kline_data[1:]
            prices = [h["close"] for h in historical if "close" in h]
            ma20 = data_service.calculate_ma(item.stock_code, prices, period=20)
            ma60 = data_service.calculate_ma(item.stock_code, prices, period=60)
            volatility = data_service.calculate_volatility(item.stock_code, prices)
            financial = data_service.get_financial_data(item.stock_code, db=db)

            data = {
                "code": current.get("code", item.stock_code),
                "name": current.get("name", item.stock_name),
                "price": current.get("price", 0),
                "pe": current.get("pe", 0),
                "pb": current.get("pb", 0),
                "volume": current.get("volume", 0),
                "ma20": ma20,
                "ma60": ma60,
                "volatility": volatility,
                **financial,
            }

            result = valuation_service.calculate(
                item.stock_code, item.model_type, data, ai_enabled=item.ai_enabled
            )
            percentile = valuation_service.calculate_percentile(
                item.stock_code, result["score"], db
            )
            status_text = valuation_service.get_status(percentile)

            results.append({
                "stock_code": item.stock_code,
                "stock_name": item.stock_name,
                "score": result["score"],
                "percentile": percentile,
                "status": status_text,
                "price": current.get("price", 0),
                "factors": result["factors"],
            })
        except Exception as e:
            results.append({
                "stock_code": item.stock_code,
                "stock_name": item.stock_name,
                "error": str(e),
            })

    return {"results": results}


@router.get("", response_model=List[WatchlistResponse])
def get_watchlist(db: Session = Depends(get_db)):
    """获取自选股列表。"""
    items = db.query(Watchlist).order_by(Watchlist.created_at.desc()).all()
    return items


@router.post("", response_model=WatchlistResponse)
def add_to_watchlist(item: WatchlistItem, db: Session = Depends(get_db)):
    """添加股票到自选列表。代码支持 000001、000001.sz、sh.000001 等格式，名称可不填自动获取。"""
    stock_code = normalize_stock_code(item.stock_code)
    stock_name = (item.stock_name or "").strip()

    # 名称未填时自动从行情接口获取
    if not stock_name:
        data_service = DataService()
        kline_data = data_service.get_kline_data(stock_code, db=db)
        if kline_data:
            stock_name = kline_data[0].get("name", "")
        if not stock_name:
            raise HTTPException(status_code=400, detail=f"无法获取股票 {stock_code} 的信息，请检查代码是否正确")

    existing = db.query(Watchlist).filter(Watchlist.stock_code == stock_code).first()
    if existing:
        raise HTTPException(status_code=400, detail="Stock already in watchlist")
    watchlist_item = Watchlist(
        stock_code=stock_code,
        stock_name=stock_name,
        industry=item.industry or "",
        model_type=item.model_type,
        ai_enabled=item.ai_enabled,
    )
    db.add(watchlist_item)
    db.commit()
    db.refresh(watchlist_item)
    return watchlist_item


@router.delete("/{code}")
def remove_from_watchlist(code: str, db: Session = Depends(get_db)):
    """从自选列表删除股票。"""
    item = db.query(Watchlist).filter(Watchlist.stock_code == code).first()
    if not item:
        raise HTTPException(status_code=404, detail="Stock not found in watchlist")
    db.delete(item)
    db.commit()
    return {"message": "Removed from watchlist"}


@router.post("/batch")
def batch_calculate(db: Session = Depends(get_db)):
    """批量计算所有自选股的估值评分。"""
    try:
        from app.services.watchlist import WatchlistService
        service = WatchlistService()
        return service.batch_calculate(db)
    except ImportError:
        return _batch_calculate(db)

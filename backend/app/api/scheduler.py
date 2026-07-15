from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models import SchedulerConfig, Watchlist
from app.services.data_service import DataService
from app.services.valuation import ValuationService
from app.schemas.scheduler import SchedulerConfig as SchedulerConfigSchema

router = APIRouter()


def _batch_calculate(db: Session) -> dict:
    """Inline batch calculation logic for watchlist stocks."""
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
            ma20 = data_service.calculate_ma(prices, period=20)
            ma60 = data_service.calculate_ma(prices, period=60)
            volatility = data_service.calculate_volatility(prices)
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


@router.get("/config", response_model=SchedulerConfigSchema)
def get_scheduler_config(db: Session = Depends(get_db)):
    config = db.query(SchedulerConfig).first()
    if not config:
        config = SchedulerConfig(
            schedule_type="daily",
            cron_expression="0 18 * * *",
            enabled=True,
            include_ai=False,
            financial_update_frequency=7,
        )
        db.add(config)
        db.commit()
        db.refresh(config)
    return config


@router.put("/config", response_model=SchedulerConfigSchema)
def update_scheduler_config(
    config_data: SchedulerConfigSchema, db: Session = Depends(get_db)
):
    config = db.query(SchedulerConfig).first()
    if not config:
        config = SchedulerConfig(
            schedule_type=config_data.schedule_type,
            cron_expression=config_data.cron_expression,
            enabled=config_data.enabled,
            include_ai=config_data.include_ai,
            financial_update_frequency=config_data.financial_update_frequency,
        )
        db.add(config)
    else:
        config.schedule_type = config_data.schedule_type
        config.cron_expression = config_data.cron_expression
        config.enabled = config_data.enabled
        config.include_ai = config_data.include_ai
        config.financial_update_frequency = config_data.financial_update_frequency
    db.commit()
    db.refresh(config)
    return config


@router.post("/run")
def trigger_batch_calculation(db: Session = Depends(get_db)):
    try:
        from app.services.watchlist import WatchlistService
        service = WatchlistService()
        return service.batch_calculate(db)
    except ImportError:
        return _batch_calculate(db)

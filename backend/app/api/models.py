from fastapi import APIRouter, HTTPException

from app.services.valuation import ValuationService

router = APIRouter()


@router.get("")
def get_models():
    service = ValuationService()
    return service.get_models()


@router.get("/factors")
def get_factors():
    service = ValuationService()
    return service.get_factors()


@router.get("/factors/{code}")
def get_factor(code: str):
    service = ValuationService()
    factors = service.get_factors()
    for factor in factors:
        if factor.get("code") == code:
            return factor
    raise HTTPException(status_code=404, detail="Factor not found")


@router.get("/{code}")
def get_model(code: str):
    service = ValuationService()
    models = service.get_models()
    for model in models:
        if model.get("code") == code:
            return model
    raise HTTPException(status_code=404, detail="Model not found")

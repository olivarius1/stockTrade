from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import auth_router, stock_router, watchlist_router, scheduler_router, models_router

app = FastAPI(title="Stock Valuation System", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
app.include_router(stock_router, prefix="/api/stock", tags=["stock"])
app.include_router(watchlist_router, prefix="/api/watchlist", tags=["watchlist"])
app.include_router(scheduler_router, prefix="/api/scheduler", tags=["scheduler"])
app.include_router(models_router, prefix="/api/models", tags=["models"])

@app.get("/")
async def root():
    return {"message": "Stock Valuation System API"}

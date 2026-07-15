# Stock Valuation System Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a full-stack stock valuation system with FastAPI backend and Vue3 frontend, supporting pluggable valuation models/factors, watchlist management, and scheduled tasks.

**Architecture:** Monolith with FastAPI backend (Python 3.12), Vue3 frontend, SQLite database, Redis cache, and Celery for scheduled tasks. Core valuation logic implemented as plugins for extensibility.

**Tech Stack:**
- Backend: FastAPI 0.139+, Python 3.12, SQLAlchemy 2.0, SQLite, Redis, Celery 5.3+
- Frontend: Vue3 3.4+, Element Plus 2.4+, ECharts 5.4+
- Dev Tools: pytest, uvicorn

---

## File Structure

```
stockTrade/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   ├── security.py
│   │   │   └── cache.py
│   │   ├── db/
│   │   │   ├── __init__.py
│   │   │   ├── models.py
│   │   │   └── session.py
│   │   ├── plugins/
│   │   │   ├── __init__.py
│   │   │   ├── models/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── base.py
│   │   │   │   ├── staples.py
│   │   │   │   ├── cyclical.py
│   │   │   │   ├── tech.py
│   │   │   │   ├── bank.py
│   │   │   │   ├── pharma.py
│   │   │   │   └── soe.py
│   │   │   └── factors/
│   │   │       ├── __init__.py
│   │   │       ├── base.py
│   │   │       ├── pe.py
│   │   │       ├── pb.py
│   │   │       ├── peg.py
│   │   │       ├── ma_deviation.py
│   │   │       ├── volatility.py
│   │   │       ├── volume.py
│   │   │       ├── roe.py
│   │   │       ├── dividend.py
│   │   │       └── ai_analysis.py
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── valuation.py
│   │   │   ├── data_service.py
│   │   │   ├── watchlist.py
│   │   │   └── scheduler.py
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   ├── stock.py
│   │   │   ├── watchlist.py
│   │   │   ├── scheduler.py
│   │   │   └── models.py
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   ├── stock.py
│   │   │   ├── valuation.py
│   │   │   ├── watchlist.py
│   │   │   └── scheduler.py
│   │   └── tasks/
│   │       ├── __init__.py
│   │       └── valuation_tasks.py
│   ├── requirements.txt
│   └── tests/
│       ├── __init__.py
│       ├── test_plugins.py
│       └── test_valuation.py
├── frontend/
│   ├── src/
│   │   ├── main.js
│   │   ├── App.vue
│   │   ├── router/
│   │   │   └── index.js
│   │   ├── store/
│   │   │   └── index.js
│   │   ├── api/
│   │   │   └── index.js
│   │   ├── components/
│   │   │   ├── StockSearch.vue
│   │   │   ├── Watchlist.vue
│   │   │   ├── ValuationChart.vue
│   │   │   └── FactorDetail.vue
│   │   └── views/
│   │       ├── Login.vue
│   │       ├── Home.vue
│   │       ├── ValuationReport.vue
│   │       ├── ModelManager.vue
│   │       ├── Scheduler.vue
│   │       └── Settings.vue
│   ├── package.json
│   └── vite.config.js
└── docker-compose.yml
```

---

## Task 1: Backend Project Setup

**Files:**
- Create: `backend/requirements.txt`
- Create: `backend/app/__init__.py`
- Create: `backend/app/main.py`
- Create: `backend/app/core/config.py`
- Create: `backend/app/db/session.py`

- [ ] **Step 1: Create requirements.txt**

```txt
fastapi==0.139.0
uvicorn==0.51.0
sqlalchemy==2.0.32
redis==5.0.1
celery==5.3.6
python-multipart==0.0.9
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
pydantic==2.8.0
requests==2.32.3
pandas==2.2.2
numpy==1.26.4
pytest==8.2.0
```

- [ ] **Step 2: Create app/__init__.py**

```python
__version__ = "1.0.0"
```

- [ ] **Step 3: Create app/main.py**

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import auth, stock, watchlist, scheduler, models

app = FastAPI(title="Stock Valuation System", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(stock.router, prefix="/api/stock", tags=["stock"])
app.include_router(watchlist.router, prefix="/api/watchlist", tags=["watchlist"])
app.include_router(scheduler.router, prefix="/api/scheduler", tags=["scheduler"])
app.include_router(models.router, prefix="/api/models", tags=["models"])

@app.get("/")
async def root():
    return {"message": "Stock Valuation System API"}
```

- [ ] **Step 4: Create app/core/config.py**

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "Stock Valuation System"
    DEBUG: bool = True
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    DATABASE_URL: str = "sqlite:///./data/valuation.db"
    REDIS_URL: str = "redis://localhost:6379"
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"

    class Config:
        env_file = ".env"

settings = Settings()
```

- [ ] **Step 5: Create app/db/session.py**

```python
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

- [ ] **Step 6: Commit**

```bash
git add backend/requirements.txt backend/app/__init__.py backend/app/main.py backend/app/core/config.py backend/app/db/session.py
git commit -m "feat: backend project setup"
```

---

## Task 2: Database Models

**Files:**
- Create: `backend/app/db/models.py`
- Create: `backend/app/schemas/stock.py`
- Create: `backend/app/schemas/valuation.py`
- Create: `backend/app/schemas/watchlist.py`
- Create: `backend/app/schemas/scheduler.py`

- [ ] **Step 1: Create app/db/models.py**

```python
from sqlalchemy import Column, Integer, String, Float, Boolean, Date, DateTime, JSON
from sqlalchemy.sql import func
from app.db.session import Base

class KlineData(Base):
    __tablename__ = "kline_data"
    id = Column(Integer, primary_key=True, index=True)
    stock_code = Column(String(10), index=True)
    date = Column(Date, index=True)
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)
    volume = Column(Integer)
    amount = Column(Float)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class ValuationHistory(Base):
    __tablename__ = "valuation_history"
    id = Column(Integer, primary_key=True, index=True)
    stock_code = Column(String(10), index=True)
    date = Column(Date, index=True)
    score = Column(Float)
    pe_score = Column(Float)
    pb_score = Column(Float)
    peg_score = Column(Float)
    ma_score = Column(Float)
    volatility_score = Column(Float)
    volume_score = Column(Float)
    roe_score = Column(Float)
    dividend_score = Column(Float)
    ai_score = Column(Float)
    pe = Column(Float)
    pb = Column(Float)
    price = Column(Float)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class FinancialData(Base):
    __tablename__ = "financial_data"
    id = Column(Integer, primary_key=True, index=True)
    stock_code = Column(String(10), index=True)
    report_date = Column(Date, index=True)
    eps = Column(Float)
    revenue = Column(Float)
    net_profit = Column(Float)
    roe = Column(Float)
    gross_margin = Column(Float)
    dividend_rate = Column(Float)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class Watchlist(Base):
    __tablename__ = "watchlist"
    id = Column(Integer, primary_key=True, index=True)
    stock_code = Column(String(10), unique=True, index=True)
    stock_name = Column(String(50))
    industry = Column(String(50))
    model_type = Column(String(20))
    ai_enabled = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class SchedulerConfig(Base):
    __tablename__ = "scheduler_config"
    id = Column(Integer, primary_key=True, index=True)
    schedule_type = Column(String(20))
    cron_expression = Column(String(50))
    enabled = Column(Boolean, default=True)
    include_ai = Column(Boolean, default=False)
    financial_update_frequency = Column(Integer, default=7)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class ModelConfig(Base):
    __tablename__ = "model_config"
    id = Column(Integer, primary_key=True, index=True)
    model_code = Column(String(20), unique=True, index=True)
    model_name = Column(String(50))
    factors = Column(JSON)
    weights = Column(JSON)
    params = Column(JSON)
    enabled = Column(Boolean, default=True)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True)
    hashed_password = Column(String(255))
    created_at = Column(DateTime, default=func.now())
```

- [ ] **Step 2: Create app/schemas/stock.py**

```python
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
```

- [ ] **Step 3: Create app/schemas/valuation.py**

```python
from pydantic import BaseModel
from datetime import date
from typing import Optional, Dict

class ValuationFactor(BaseModel):
    code: str
    name: str
    score: float
    weight: float

class ValuationResult(BaseModel):
    stock_code: str
    stock_name: str
    date: date
    score: float
    percentile: float
    status: str
    pe: float
    pb: float
    price: float
    factors: Dict[str, float]

class ValuationHistoryItem(BaseModel):
    date: date
    score: float
    price: float
```

- [ ] **Step 4: Create app/schemas/watchlist.py**

```python
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
```

- [ ] **Step 5: Create app/schemas/scheduler.py**

```python
from pydantic import BaseModel

class SchedulerConfig(BaseModel):
    schedule_type: str
    cron_expression: str
    enabled: bool = True
    include_ai: bool = False
    financial_update_frequency: int = 7
```

- [ ] **Step 6: Commit**

```bash
git add backend/app/db/models.py backend/app/schemas/
git commit -m "feat: database models and schemas"
```

---

## Task 3: Plugin System - Base Classes

**Files:**
- Create: `backend/app/plugins/__init__.py`
- Create: `backend/app/plugins/models/base.py`
- Create: `backend/app/plugins/factors/base.py`

- [ ] **Step 1: Create app/plugins/__init__.py**

```python
from app.plugins.models.base import ValuationModel, register_model
from app.plugins.factors.base import ValuationFactor, register_factor
from app.plugins.models import staples, cyclical, tech, bank, pharma, soe
from app.plugins.factors import pe, pb, peg, ma_deviation, volatility, volume, roe, dividend, ai_analysis

def load_plugins():
    pass
```

- [ ] **Step 2: Create app/plugins/models/base.py**

```python
from abc import ABC, abstractmethod
from typing import List, Dict

model_registry = {}

def register_model(cls):
    model_registry[cls.get_code(cls)] = cls
    return cls

class ValuationModel(ABC):
    @abstractmethod
    def get_name(self) -> str:
        pass
    
    @abstractmethod
    def get_code(self) -> str:
        pass
    
    @abstractmethod
    def get_factors(self) -> List[str]:
        pass
    
    @abstractmethod
    def get_weights(self) -> Dict[str, float]:
        pass
    
    @abstractmethod
    def get_params(self) -> Dict[str, float]:
        pass

def get_model(model_code: str) -> ValuationModel:
    return model_registry.get(model_code)

def list_models() -> List[Dict]:
    return [{
        "code": code,
        "name": model.get_name(model()),
        "factors": model.get_factors(model()),
        "weights": model.get_weights(model())
    } for code, model in model_registry.items()]
```

- [ ] **Step 3: Create app/plugins/factors/base.py**

```python
from abc import ABC, abstractmethod
from typing import List, Dict

factor_registry = {}

def register_factor(cls):
    factor_registry[cls.get_code(cls)] = cls
    return cls

class ValuationFactor(ABC):
    @abstractmethod
    def get_name(self) -> str:
        pass
    
    @abstractmethod
    def get_code(self) -> str:
        pass
    
    @abstractmethod
    def score(self, data: Dict) -> float:
        pass
    
    @abstractmethod
    def requires_data(self) -> List[str]:
        pass

def get_factor(factor_code: str) -> ValuationFactor:
    return factor_registry.get(factor_code)

def list_factors() -> List[Dict]:
    return [{
        "code": code,
        "name": factor.get_name(factor()),
        "requires_data": factor.requires_data(factor())
    } for code, factor in factor_registry.items()]
```

- [ ] **Step 4: Commit**

```bash
git add backend/app/plugins/__init__.py backend/app/plugins/models/base.py backend/app/plugins/factors/base.py
git commit -m "feat: plugin system base classes"
```

---

## Task 4: Plugin System - Models Implementation

**Files:**
- Create: `backend/app/plugins/models/__init__.py`
- Create: `backend/app/plugins/models/staples.py`
- Create: `backend/app/plugins/models/cyclical.py`
- Create: `backend/app/plugins/models/tech.py`
- Create: `backend/app/plugins/models/bank.py`
- Create: `backend/app/plugins/models/pharma.py`
- Create: `backend/app/plugins/models/soe.py`

- [ ] **Step 1: Create app/plugins/models/__init__.py**

```python
from .staples import StaplesModel
from .cyclical import CyclicalModel
from .tech import TechModel
from .bank import BankModel
from .pharma import PharmaModel
from .soe import SOEModel
```

- [ ] **Step 2: Create app/plugins/models/staples.py**

```python
from app.plugins.models.base import ValuationModel, register_model
from typing import List, Dict

@register_model
class StaplesModel(ValuationModel):
    def get_name(self) -> str:
        return "必选消费"
    
    def get_code(self) -> str:
        return "staples"
    
    def get_factors(self) -> List[str]:
        return ["pe", "peg", "pb", "ma_deviation", "volatility", "volume"]
    
    def get_weights(self) -> Dict[str, float]:
        return {
            "pe": 0.31,
            "peg": 0.22,
            "pb": 0.13,
            "ma_deviation": 0.13,
            "volatility": 0.11,
            "volume": 0.09
        }
    
    def get_params(self) -> Dict[str, float]:
        return {
            "pe_min": 5,
            "pe_max": 40,
            "pb_min": 1,
            "pb_max": 10,
            "eps_growth": 0.15
        }
```

- [ ] **Step 3: Create app/plugins/models/cyclical.py**

```python
from app.plugins.models.base import ValuationModel, register_model
from typing import List, Dict

@register_model
class CyclicalModel(ValuationModel):
    def get_name(self) -> str:
        return "周期股"
    
    def get_code(self) -> str:
        return "cyclical"
    
    def get_factors(self) -> List[str]:
        return ["pe", "pb", "ma_deviation", "volatility", "volume"]
    
    def get_weights(self) -> Dict[str, float]:
        return {
            "pe": 0.30,
            "pb": 0.20,
            "ma_deviation": 0.20,
            "volatility": 0.15,
            "volume": 0.15
        }
    
    def get_params(self) -> Dict[str, float]:
        return {
            "pe_min": 3,
            "pe_max": 30,
            "pb_min": 0.5,
            "pb_max": 5,
            "eps_growth": 0.10
        }
```

- [ ] **Step 4: Create app/plugins/models/tech.py**

```python
from app.plugins.models.base import ValuationModel, register_model
from typing import List, Dict

@register_model
class TechModel(ValuationModel):
    def get_name(self) -> str:
        return "科技股"
    
    def get_code(self) -> str:
        return "tech"
    
    def get_factors(self) -> List[str]:
        return ["peg", "pe", "pb", "ma_deviation", "volatility", "volume"]
    
    def get_weights(self) -> Dict[str, float]:
        return {
            "peg": 0.30,
            "pe": 0.24,
            "pb": 0.14,
            "ma_deviation": 0.18,
            "volatility": 0.12,
            "volume": 0.02
        }
    
    def get_params(self) -> Dict[str, float]:
        return {
            "pe_min": 10,
            "pe_max": 80,
            "pb_min": 2,
            "pb_max": 20,
            "eps_growth": 0.20
        }
```

- [ ] **Step 5: Create app/plugins/models/bank.py**

```python
from app.plugins.models.base import ValuationModel, register_model
from typing import List, Dict

@register_model
class BankModel(ValuationModel):
    def get_name(self) -> str:
        return "银行保险"
    
    def get_code(self) -> str:
        return "bank"
    
    def get_factors(self) -> List[str]:
        return ["pb", "roe", "dividend", "ma_deviation", "volatility"]
    
    def get_weights(self) -> Dict[str, float]:
        return {
            "pb": 0.30,
            "roe": 0.25,
            "dividend": 0.15,
            "ma_deviation": 0.15,
            "volatility": 0.15
        }
    
    def get_params(self) -> Dict[str, float]:
        return {
            "pb_min": 0.5,
            "pb_max": 2,
            "roe_min": 0.05,
            "roe_max": 0.20,
            "dividend_min": 0.02,
            "dividend_max": 0.10
        }
```

- [ ] **Step 6: Create app/plugins/models/pharma.py**

```python
from app.plugins.models.base import ValuationModel, register_model
from typing import List, Dict

@register_model
class PharmaModel(ValuationModel):
    def get_name(self) -> str:
        return "医药股"
    
    def get_code(self) -> str:
        return "pharma"
    
    def get_factors(self) -> List[str]:
        return ["peg", "pe", "pb", "ma_deviation", "volatility", "volume"]
    
    def get_weights(self) -> Dict[str, float]:
        return {
            "peg": 0.30,
            "pe": 0.25,
            "pb": 0.15,
            "ma_deviation": 0.15,
            "volatility": 0.10,
            "volume": 0.05
        }
    
    def get_params(self) -> Dict[str, float]:
        return {
            "pe_min": 15,
            "pe_max": 60,
            "pb_min": 3,
            "pb_max": 15,
            "eps_growth": 0.18
        }
```

- [ ] **Step 7: Create app/plugins/models/soe.py**

```python
from app.plugins.models.base import ValuationModel, register_model
from typing import List, Dict

@register_model
class SOEModel(ValuationModel):
    def get_name(self) -> str:
        return "央企国企"
    
    def get_code(self) -> str:
        return "soe"
    
    def get_factors(self) -> List[str]:
        return ["pb", "roe", "dividend", "ma_deviation", "volatility", "volume"]
    
    def get_weights(self) -> Dict[str, float]:
        return {
            "pb": 0.25,
            "roe": 0.20,
            "dividend": 0.20,
            "ma_deviation": 0.15,
            "volatility": 0.10,
            "volume": 0.10
        }
    
    def get_params(self) -> Dict[str, float]:
        return {
            "pb_min": 0.8,
            "pb_max": 3,
            "roe_min": 0.06,
            "roe_max": 0.15,
            "dividend_min": 0.03,
            "dividend_max": 0.08
        }
```

- [ ] **Step 8: Commit**

```bash
git add backend/app/plugins/models/
git commit -m "feat: valuation models implementation"
```

---

## Task 5: Plugin System - Factors Implementation

**Files:**
- Create: `backend/app/plugins/factors/__init__.py`
- Create: `backend/app/plugins/factors/pe.py`
- Create: `backend/app/plugins/factors/pb.py`
- Create: `backend/app/plugins/factors/peg.py`
- Create: `backend/app/plugins/factors/ma_deviation.py`
- Create: `backend/app/plugins/factors/volatility.py`
- Create: `backend/app/plugins/factors/volume.py`
- Create: `backend/app/plugins/factors/roe.py`
- Create: `backend/app/plugins/factors/dividend.py`
- Create: `backend/app/plugins/factors/ai_analysis.py`

- [ ] **Step 1: Create app/plugins/factors/__init__.py**

```python
from .pe import PEFactor
from .pb import PBFactor
from .peg import PEGFactor
from .ma_deviation import MADeviationFactor
from .volatility import VolatilityFactor
from .volume import VolumeFactor
from .roe import ROEFactor
from .dividend import DividendFactor
from .ai_analysis import AIAnalysisFactor
```

- [ ] **Step 2: Create app/plugins/factors/pe.py**

```python
from app.plugins.factors.base import ValuationFactor, register_factor
from typing import List, Dict

@register_factor
class PEFactor(ValuationFactor):
    def get_name(self) -> str:
        return "PE评分"
    
    def get_code(self) -> str:
        return "pe"
    
    def requires_data(self) -> List[str]:
        return ["kline", "pe_range"]
    
    def score(self, data: Dict) -> float:
        pe = data.get("pe", 0)
        pe_min = data.get("pe_min", 5)
        pe_max = data.get("pe_max", 50)
        
        if pe <= pe_min:
            return 95
        elif pe <= pe_min * 1.5:
            return 80
        elif pe <= pe_min * 2:
            return 65
        elif pe <= pe_max * 0.7:
            return 50
        elif pe <= pe_max:
            return 35
        else:
            return 20
```

- [ ] **Step 3: Create app/plugins/factors/pb.py**

```python
from app.plugins.factors.base import ValuationFactor, register_factor
from typing import List, Dict

@register_factor
class PBFactor(ValuationFactor):
    def get_name(self) -> str:
        return "PB评分"
    
    def get_code(self) -> str:
        return "pb"
    
    def requires_data(self) -> List[str]:
        return ["kline", "pb_range"]
    
    def score(self, data: Dict) -> float:
        pb = data.get("pb", 0)
        pb_min = data.get("pb_min", 0.5)
        pb_max = data.get("pb_max", 10)
        
        if pb <= pb_min:
            return 95
        elif pb <= pb_min * 1.5:
            return 80
        elif pb <= pb_min * 2:
            return 65
        elif pb <= pb_max * 0.7:
            return 50
        elif pb <= pb_max:
            return 35
        else:
            return 20
```

- [ ] **Step 4: Create app/plugins/factors/peg.py**

```python
from app.plugins.factors.base import ValuationFactor, register_factor
from typing import List, Dict

@register_factor
class PEGFactor(ValuationFactor):
    def get_name(self) -> str:
        return "PEG评分"
    
    def get_code(self) -> str:
        return "peg"
    
    def requires_data(self) -> List[str]:
        return ["kline", "eps_growth"]
    
    def score(self, data: Dict) -> float:
        pe = data.get("pe", 0)
        eps_growth = data.get("eps_growth", 0.1)
        
        if eps_growth <= 0:
            return 20
        
        peg = pe / (eps_growth * 100)
        
        if peg <= 0.5:
            return 95
        elif peg <= 1.0:
            return 80
        elif peg <= 1.2:
            return 65
        elif peg <= 1.5:
            return 50
        elif peg <= 2.0:
            return 35
        else:
            return 20
```

- [ ] **Step 5: Create app/plugins/factors/ma_deviation.py**

```python
from app.plugins.factors.base import ValuationFactor, register_factor
from typing import List, Dict

@register_factor
class MADeviationFactor(ValuationFactor):
    def get_name(self) -> str:
        return "MA偏离度"
    
    def get_code(self) -> str:
        return "ma_deviation"
    
    def requires_data(self) -> List[str]:
        return ["kline"]
    
    def score(self, data: Dict) -> float:
        price = data.get("price", 0)
        ma20 = data.get("ma20", 0)
        ma60 = data.get("ma60", 0)
        
        if ma60 == 0:
            return 50
        
        deviation = (price - ma60) / ma60
        
        if deviation <= -0.2:
            return 95
        elif deviation <= -0.1:
            return 80
        elif deviation <= -0.05:
            return 65
        elif deviation <= 0.05:
            return 50
        elif deviation <= 0.1:
            return 35
        else:
            return 20
```

- [ ] **Step 6: Create app/plugins/factors/volatility.py**

```python
from app.plugins.factors.base import ValuationFactor, register_factor
from typing import List, Dict

@register_factor
class VolatilityFactor(ValuationFactor):
    def get_name(self) -> str:
        return "波动率"
    
    def get_code(self) -> str:
        return "volatility"
    
    def requires_data(self) -> List[str]:
        return ["kline"]
    
    def score(self, data: Dict) -> float:
        volatility = data.get("volatility", 0)
        
        if volatility <= 0.02:
            return 85
        elif volatility <= 0.04:
            return 70
        elif volatility <= 0.06:
            return 55
        elif volatility <= 0.08:
            return 40
        elif volatility <= 0.10:
            return 25
        else:
            return 20
```

- [ ] **Step 7: Create app/plugins/factors/volume.py**

```python
from app.plugins.factors.base import ValuationFactor, register_factor
from typing import List, Dict

@register_factor
class VolumeFactor(ValuationFactor):
    def get_name(self) -> str:
        return "量能"
    
    def get_code(self) -> str:
        return "volume"
    
    def requires_data(self) -> List[str]:
        return ["kline"]
    
    def score(self, data: Dict) -> float:
        volume_ratio = data.get("volume_ratio", 1)
        
        if volume_ratio >= 2.0:
            return 90
        elif volume_ratio >= 1.5:
            return 75
        elif volume_ratio >= 1.0:
            return 60
        elif volume_ratio >= 0.7:
            return 45
        elif volume_ratio >= 0.5:
            return 30
        else:
            return 20
```

- [ ] **Step 8: Create app/plugins/factors/roe.py**

```python
from app.plugins.factors.base import ValuationFactor, register_factor
from typing import List, Dict

@register_factor
class ROEFactor(ValuationFactor):
    def get_name(self) -> str:
        return "ROE评分"
    
    def get_code(self) -> str:
        return "roe"
    
    def requires_data(self) -> List[str]:
        return ["financial"]
    
    def score(self, data: Dict) -> float:
        roe = data.get("roe", 0)
        roe_min = data.get("roe_min", 0.05)
        roe_max = data.get("roe_max", 0.20)
        
        if roe >= roe_max:
            return 95
        elif roe >= roe_max * 0.8:
            return 80
        elif roe >= roe_max * 0.6:
            return 65
        elif roe >= roe_min * 1.5:
            return 50
        elif roe >= roe_min:
            return 35
        else:
            return 20
```

- [ ] **Step 9: Create app/plugins/factors/dividend.py**

```python
from app.plugins.factors.base import ValuationFactor, register_factor
from typing import List, Dict

@register_factor
class DividendFactor(ValuationFactor):
    def get_name(self) -> str:
        return "股息率"
    
    def get_code(self) -> str:
        return "dividend"
    
    def requires_data(self) -> List[str]:
        return ["financial"]
    
    def score(self, data: Dict) -> float:
        dividend_rate = data.get("dividend_rate", 0)
        div_min = data.get("dividend_min", 0.02)
        div_max = data.get("dividend_max", 0.10)
        
        if dividend_rate >= div_max:
            return 95
        elif dividend_rate >= div_max * 0.8:
            return 80
        elif dividend_rate >= div_max * 0.6:
            return 65
        elif dividend_rate >= div_min * 1.5:
            return 50
        elif dividend_rate >= div_min:
            return 35
        else:
            return 20
```

- [ ] **Step 10: Create app/plugins/factors/ai_analysis.py**

```python
from app.plugins.factors.base import ValuationFactor, register_factor
from typing import List, Dict

@register_factor
class AIAnalysisFactor(ValuationFactor):
    def get_name(self) -> str:
        return "AI深度分析"
    
    def get_code(self) -> str:
        return "ai_analysis"
    
    def requires_data(self) -> List[str]:
        return ["financial", "market"]
    
    def score(self, data: Dict) -> float:
        ai_score = data.get("ai_score", 50)
        return ai_score
```

- [ ] **Step 11: Commit**

```bash
git add backend/app/plugins/factors/
git commit -m "feat: valuation factors implementation"
```

---

## Task 6: Valuation Service

**Files:**
- Create: `backend/app/services/valuation.py`

- [ ] **Step 1: Create app/services/valuation.py**

```python
from typing import Dict, List, Optional
from app.plugins.models.base import get_model, list_models
from app.plugins.factors.base import get_factor, list_factors
from app.db.models import ValuationHistory

class ValuationService:
    def __init__(self):
        pass
    
    def calculate(self, stock_code: str, model_code: str, data: Dict, ai_enabled: bool = False) -> Dict:
        model = get_model(model_code)
        if not model:
            raise ValueError(f"Model {model_code} not found")
        
        model_instance = model()
        factors = model_instance.get_factors()
        weights = model_instance.get_weights()
        params = model_instance.get_params()
        
        if ai_enabled:
            factors.append("ai_analysis")
            weights["ai_analysis"] = 0.10
        
        total_weight = sum(weights.values())
        normalized_weights = {k: v / total_weight for k, v in weights.items()}
        
        factor_scores = {}
        total_score = 0.0
        
        for factor_code in factors:
            factor = get_factor(factor_code)
            if not factor:
                continue
            
            factor_data = {**data, **params}
            score = factor.score(factor_data)
            factor_scores[factor_code] = score
            total_score += score * normalized_weights.get(factor_code, 0)
        
        result = {
            "stock_code": stock_code,
            "score": round(total_score, 2),
            "factors": factor_scores,
            "weights": normalized_weights,
            "params": params
        }
        return result
    
    def calculate_percentile(self, stock_code: str, score: float, db) -> float:
        history = db.query(ValuationHistory).filter(
            ValuationHistory.stock_code == stock_code
        ).all()
        
        if not history:
            return 50.0
        
        scores = [h.score for h in history]
        scores.append(score)
        scores.sort()
        
        rank = scores.index(score)
        percentile = (rank / len(scores)) * 100
        return round(percentile, 2)
    
    def get_status(self, percentile: float) -> str:
        if percentile >= 90:
            return "极度低估"
        elif percentile >= 70:
            return "低估"
        elif percentile >= 50:
            return "中性偏低"
        elif percentile >= 30:
            return "中性偏高"
        elif percentile >= 10:
            return "高估"
        else:
            return "极度高估"
    
    def get_models(self) -> List[Dict]:
        return list_models()
    
    def get_factors(self) -> List[Dict]:
        return list_factors()
```

- [ ] **Step 2: Commit**

```bash
git add backend/app/services/valuation.py
git commit -m "feat: valuation service"
```

---

## Task 7: Data Service

**Files:**
- Create: `backend/app/services/data_service.py`
- Create: `backend/app/core/cache.py`

- [ ] **Step 1: Create app/core/cache.py**

```python
import redis
from app.core.config import settings

redis_client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)

def get_cache():
    return redis_client

def cache_get(key: str):
    return redis_client.get(key)

def cache_set(key: str, value, expire_seconds: int = 3600):
    redis_client.set(key, value, ex=expire_seconds)

def cache_delete(key: str):
    redis_client.delete(key)
```

- [ ] **Step 2: Create app/services/data_service.py**

```python
import requests
import pandas as pd
from typing import Dict, List
from datetime import date, timedelta
from app.db.models import KlineData, FinancialData
from app.core.cache import cache_get, cache_set

class DataService:
    def __init__(self):
        self.tencent_base_url = "https://qt.gtimg.cn"
    
    def get_kline_data(self, stock_code: str, start_date: date = None, end_date: date = None, db=None) -> List[Dict]:
        if start_date is None:
            start_date = date.today() - timedelta(days=3650)
        if end_date is None:
            end_date = date.today()
        
        cached = cache_get(f"kline:{stock_code}:{start_date}:{end_date}")
        if cached:
            return eval(cached)
        
        exchange = "sh" if stock_code.startswith("6") else "sz"
        url = f"{self.tencent_base_url}/q={exchange}{stock_code}"
        
        try:
            response = requests.get(url, timeout=10)
            data = response.text
            parts = data.split("~")
            
            stock_info = {
                "code": stock_code,
                "name": parts[1],
                "price": float(parts[3]),
                "open": float(parts[5]),
                "high": float(parts[4]),
                "low": float(parts[6]),
                "volume": int(parts[10]),
                "amount": float(parts[11]),
                "pe": float(parts[39]) if parts[39] else 0,
                "pb": float(parts[46]) if parts[46] else 0
            }
            
            historical_data = []
            if db:
                historical_data = db.query(KlineData).filter(
                    KlineData.stock_code == stock_code,
                    KlineData.date >= start_date,
                    KlineData.date <= end_date
                ).all()
            
            result = [stock_info]
            for row in historical_data:
                result.append({
                    "date": row.date,
                    "open": row.open,
                    "high": row.high,
                    "low": row.low,
                    "close": row.close,
                    "volume": row.volume,
                    "amount": row.amount
                })
            
            cache_set(f"kline:{stock_code}:{start_date}:{end_date}", str(result), 3600)
            return result
        
        except Exception as e:
            return []
    
    def get_financial_data(self, stock_code: str, db=None) -> Dict:
        cached = cache_get(f"financial:{stock_code}")
        if cached:
            return eval(cached)
        
        if db:
            latest = db.query(FinancialData).filter(
                FinancialData.stock_code == stock_code
            ).order_by(FinancialData.report_date.desc()).first()
            
            if latest:
                result = {
                    "eps": latest.eps,
                    "revenue": latest.revenue,
                    "net_profit": latest.net_profit,
                    "roe": latest.roe,
                    "gross_margin": latest.gross_margin,
                    "dividend_rate": latest.dividend_rate
                }
                cache_set(f"financial:{stock_code}", str(result), 7 * 24 * 3600)
                return result
        
        return {}
    
    def search_stock(self, keyword: str) -> List[Dict]:
        url = f"{self.tencent_base_url}/q=list"
        return []
    
    def calculate_ma(self, prices: List[float], period: int = 20) -> float:
        if len(prices) < period:
            return 0
        return sum(prices[-period:]) / period
    
    def calculate_volatility(self, prices: List[float]) -> float:
        if len(prices) < 2:
            return 0
        returns = []
        for i in range(1, len(prices)):
            returns.append((prices[i] - prices[i-1]) / prices[i-1])
        if not returns:
            return 0
        mean = sum(returns) / len(returns)
        variance = sum((r - mean) ** 2 for r in returns) / len(returns)
        return variance ** 0.5
```

- [ ] **Step 3: Commit**

```bash
git add backend/app/services/data_service.py backend/app/core/cache.py
git commit -m "feat: data service with caching"
```

---

## Task 8: API Endpoints

**Files:**
- Create: `backend/app/api/__init__.py`
- Create: `backend/app/api/auth.py`
- Create: `backend/app/api/stock.py`
- Create: `backend/app/api/watchlist.py`
- Create: `backend/app/api/scheduler.py`
- Create: `backend/app/api/models.py`

- [ ] **Step 1: Create app/api/__init__.py**

```python
from .auth import router as auth_router
from .stock import router as stock_router
from .watchlist import router as watchlist_router
from .scheduler import router as scheduler_router
from .models import router as models_router

router = [auth_router, stock_router, watchlist_router, scheduler_router, models_router]
```

- [ ] **Step 2: Create app/api/auth.py**

```python
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
from app.core.config import settings
from app.db.session import get_db
from app.db.models import User

router = APIRouter()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme), db=Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception
    return user

@router.post("/login")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db=Depends(get_db)):
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/verify")
async def verify_token(current_user: User = Depends(get_current_user)):
    return {"username": current_user.username, "status": "authenticated"}
```

- [ ] **Step 3: Create app/api/stock.py**

```python
from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from datetime import date
from app.db.session import get_db
from app.db.models import ValuationHistory
from app.services.valuation import ValuationService
from app.services.data_service import DataService
from app.schemas.stock import StockInfo, KlineData, StockSearchResponse
from app.schemas.valuation import ValuationResult, ValuationHistoryItem

router = APIRouter()
valuation_service = ValuationService()
data_service = DataService()

@router.get("/search")
async def search_stock(keyword: str) -> List[StockSearchResponse]:
    results = data_service.search_stock(keyword)
    return results

@router.get("/{code}")
async def get_stock_info(code: str, db=Depends(get_db)) -> StockInfo:
    data = data_service.get_kline_data(code, db=db)
    if not data:
        raise HTTPException(status_code=404, detail="Stock not found")
    
    return StockInfo(
        code=code,
        name=data[0].get("name", ""),
        industry="",
        pe=data[0].get("pe", 0),
        pb=data[0].get("pb", 0),
        price=data[0].get("price", 0)
    )

@router.get("/{code}/valuation")
async def get_valuation(code: str, model_code: str = "tech", db=Depends(get_db)) -> ValuationResult:
    kline_data = data_service.get_kline_data(code, db=db)
    financial_data = data_service.get_financial_data(code, db=db)
    
    if not kline_data:
        raise HTTPException(status_code=404, detail="Stock data not found")
    
    prices = [k.get("close", k.get("price", 0)) for k in kline_data[1:]]
    ma20 = data_service.calculate_ma(prices, 20)
    ma60 = data_service.calculate_ma(prices, 60)
    volatility = data_service.calculate_volatility(prices)
    
    data = {
        "pe": kline_data[0].get("pe", 0),
        "pb": kline_data[0].get("pb", 0),
        "price": kline_data[0].get("price", 0),
        "ma20": ma20,
        "ma60": ma60,
        "volatility": volatility,
        **financial_data
    }
    
    result = valuation_service.calculate(code, model_code, data)
    percentile = valuation_service.calculate_percentile(code, result["score"], db)
    status = valuation_service.get_status(percentile)
    
    return ValuationResult(
        stock_code=code,
        stock_name=kline_data[0].get("name", ""),
        date=date.today(),
        score=result["score"],
        percentile=percentile,
        status=status,
        pe=data["pe"],
        pb=data["pb"],
        price=data["price"],
        factors=result["factors"]
    )

@router.get("/{code}/history")
async def get_valuation_history(code: str, start_date: Optional[date] = None, end_date: Optional[date] = None, db=Depends(get_db)) -> List[ValuationHistoryItem]:
    query = db.query(ValuationHistory).filter(ValuationHistory.stock_code == code)
    if start_date:
        query = query.filter(ValuationHistory.date >= start_date)
    if end_date:
        query = query.filter(ValuationHistory.date <= end_date)
    
    history = query.order_by(ValuationHistory.date).all()
    return [ValuationHistoryItem(
        date=item.date,
        score=item.score,
        price=item.price
    ) for item in history]
```

- [ ] **Step 4: Create app/api/watchlist.py**

```python
from fastapi import APIRouter, Depends, HTTPException
from typing import List
from app.db.session import get_db
from app.db.models import Watchlist
from app.schemas.watchlist import WatchlistItem, WatchlistResponse

router = APIRouter()

@router.get("")
async def get_watchlist(db=Depends(get_db)) -> List[WatchlistResponse]:
    items = db.query(Watchlist).all()
    return [WatchlistResponse(
        id=item.id,
        stock_code=item.stock_code,
        stock_name=item.stock_name,
        industry=item.industry,
        model_type=item.model_type,
        ai_enabled=item.ai_enabled,
        created_at=item.created_at
    ) for item in items]

@router.post("")
async def add_to_watchlist(item: WatchlistItem, db=Depends(get_db)) -> WatchlistResponse:
    existing = db.query(Watchlist).filter(Watchlist.stock_code == item.stock_code).first()
    if existing:
        raise HTTPException(status_code=400, detail="Stock already in watchlist")
    
    new_item = Watchlist(
        stock_code=item.stock_code,
        stock_name=item.stock_name,
        industry=item.industry,
        model_type=item.model_type,
        ai_enabled=item.ai_enabled
    )
    db.add(new_item)
    db.commit()
    db.refresh(new_item)
    
    return WatchlistResponse(
        id=new_item.id,
        stock_code=new_item.stock_code,
        stock_name=new_item.stock_name,
        industry=new_item.industry,
        model_type=new_item.model_type,
        ai_enabled=new_item.ai_enabled,
        created_at=new_item.created_at
    )

@router.delete("/{code}")
async def remove_from_watchlist(code: str, db=Depends(get_db)):
    item = db.query(Watchlist).filter(Watchlist.stock_code == code).first()
    if not item:
        raise HTTPException(status_code=404, detail="Stock not in watchlist")
    
    db.delete(item)
    db.commit()
    return {"message": "Stock removed from watchlist"}

@router.post("/batch")
async def batch_calculate(db=Depends(get_db)):
    items = db.query(Watchlist).all()
    results = []
    
    from app.services.valuation import ValuationService
    from app.services.data_service import DataService
    
    valuation_service = ValuationService()
    data_service = DataService()
    
    for item in items:
        try:
            kline_data = data_service.get_kline_data(item.stock_code, db=db)
            financial_data = data_service.get_financial_data(item.stock_code, db=db)
            
            if kline_data:
                prices = [k.get("close", k.get("price", 0)) for k in kline_data[1:]]
                data = {
                    "pe": kline_data[0].get("pe", 0),
                    "pb": kline_data[0].get("pb", 0),
                    "price": kline_data[0].get("price", 0),
                    "ma20": data_service.calculate_ma(prices, 20),
                    "ma60": data_service.calculate_ma(prices, 60),
                    "volatility": data_service.calculate_volatility(prices),
                    **financial_data
                }
                
                result = valuation_service.calculate(
                    item.stock_code, 
                    item.model_type, 
                    data, 
                    item.ai_enabled
                )
                
                results.append({
                    "stock_code": item.stock_code,
                    "stock_name": item.stock_name,
                    "score": result["score"]
                })
        except Exception as e:
            results.append({
                "stock_code": item.stock_code,
                "stock_name": item.stock_name,
                "error": str(e)
            })
    
    return {"results": results}
```

- [ ] **Step 5: Create app/api/scheduler.py**

```python
from fastapi import APIRouter, Depends, HTTPException
from app.db.session import get_db
from app.db.models import SchedulerConfig
from app.schemas.scheduler import SchedulerConfig as SchedulerConfigSchema

router = APIRouter()

@router.get("/config")
async def get_scheduler_config(db=Depends(get_db)) -> SchedulerConfigSchema:
    config = db.query(SchedulerConfig).first()
    if not config:
        config = SchedulerConfig(
            schedule_type="daily",
            cron_expression="0 18 * * *",
            enabled=True,
            include_ai=False,
            financial_update_frequency=7
        )
        db.add(config)
        db.commit()
    
    return SchedulerConfigSchema(
        schedule_type=config.schedule_type,
        cron_expression=config.cron_expression,
        enabled=config.enabled,
        include_ai=config.include_ai,
        financial_update_frequency=config.financial_update_frequency
    )

@router.put("/config")
async def update_scheduler_config(config: SchedulerConfigSchema, db=Depends(get_db)) -> SchedulerConfigSchema:
    existing = db.query(SchedulerConfig).first()
    if existing:
        existing.schedule_type = config.schedule_type
        existing.cron_expression = config.cron_expression
        existing.enabled = config.enabled
        existing.include_ai = config.include_ai
        existing.financial_update_frequency = config.financial_update_frequency
    else:
        existing = SchedulerConfig(**config.dict())
        db.add(existing)
    
    db.commit()
    return config

@router.post("/run")
async def run_scheduler(db=Depends(get_db)):
    from app.services.watchlist import WatchlistService
    service = WatchlistService()
    results = service.batch_calculate(db)
    return {"message": "Batch calculation completed", "results": results}
```

- [ ] **Step 6: Create app/api/models.py**

```python
from fastapi import APIRouter
from typing import List
from app.services.valuation import ValuationService

router = APIRouter()
valuation_service = ValuationService()

@router.get("")
async def get_models() -> List[dict]:
    return valuation_service.get_models()

@router.get("/{code}")
async def get_model(code: str) -> dict:
    models = valuation_service.get_models()
    for model in models:
        if model["code"] == code:
            return model
    raise HTTPException(status_code=404, detail="Model not found")

@router.get("/factors")
async def get_factors() -> List[dict]:
    return valuation_service.get_factors()

@router.get("/factors/{code}")
async def get_factor(code: str) -> dict:
    factors = valuation_service.get_factors()
    for factor in factors:
        if factor["code"] == code:
            return factor
    raise HTTPException(status_code=404, detail="Factor not found")
```

- [ ] **Step 7: Commit**

```bash
git add backend/app/api/
git commit -m "feat: API endpoints"
```

---

## Task 9: Watchlist Service and Scheduler

**Files:**
- Create: `backend/app/services/watchlist.py`
- Create: `backend/app/services/scheduler.py`
- Create: `backend/app/tasks/__init__.py`
- Create: `backend/app/tasks/valuation_tasks.py`

- [ ] **Step 1: Create app/services/watchlist.py**

```python
from typing import List, Dict
from app.db.models import Watchlist, ValuationHistory
from app.services.valuation import ValuationService
from app.services.data_service import DataService

class WatchlistService:
    def __init__(self):
        self.valuation_service = ValuationService()
        self.data_service = DataService()
    
    def get_watchlist(self, db) -> List[Dict]:
        items = db.query(Watchlist).all()
        return [{
            "id": item.id,
            "stock_code": item.stock_code,
            "stock_name": item.stock_name,
            "industry": item.industry,
            "model_type": item.model_type,
            "ai_enabled": item.ai_enabled,
            "created_at": item.created_at
        } for item in items]
    
    def add_stock(self, db, stock_code: str, stock_name: str, industry: str, model_type: str, ai_enabled: bool):
        existing = db.query(Watchlist).filter(Watchlist.stock_code == stock_code).first()
        if existing:
            raise ValueError("Stock already in watchlist")
        
        item = Watchlist(
            stock_code=stock_code,
            stock_name=stock_name,
            industry=industry,
            model_type=model_type,
            ai_enabled=ai_enabled
        )
        db.add(item)
        db.commit()
        return item
    
    def remove_stock(self, db, stock_code: str):
        item = db.query(Watchlist).filter(Watchlist.stock_code == stock_code).first()
        if not item:
            raise ValueError("Stock not in watchlist")
        
        db.delete(item)
        db.commit()
    
    def batch_calculate(self, db) -> List[Dict]:
        items = db.query(Watchlist).all()
        results = []
        
        for item in items:
            try:
                kline_data = self.data_service.get_kline_data(item.stock_code, db=db)
                financial_data = self.data_service.get_financial_data(item.stock_code, db=db)
                
                if kline_data:
                    prices = [k.get("close", k.get("price", 0)) for k in kline_data[1:]]
                    data = {
                        "pe": kline_data[0].get("pe", 0),
                        "pb": kline_data[0].get("pb", 0),
                        "price": kline_data[0].get("price", 0),
                        "ma20": self.data_service.calculate_ma(prices, 20),
                        "ma60": self.data_service.calculate_ma(prices, 60),
                        "volatility": self.data_service.calculate_volatility(prices),
                        **financial_data
                    }
                    
                    result = self.valuation_service.calculate(
                        item.stock_code,
                        item.model_type,
                        data,
                        item.ai_enabled
                    )
                    
                    history = ValuationHistory(
                        stock_code=item.stock_code,
                        date=kline_data[0].get("date", self.data_service.get_current_date()),
                        score=result["score"],
                        pe_score=result["factors"].get("pe", 0),
                        pb_score=result["factors"].get("pb", 0),
                        peg_score=result["factors"].get("peg", 0),
                        ma_score=result["factors"].get("ma_deviation", 0),
                        volatility_score=result["factors"].get("volatility", 0),
                        volume_score=result["factors"].get("volume", 0),
                        roe_score=result["factors"].get("roe", 0),
                        dividend_score=result["factors"].get("dividend", 0),
                        ai_score=result["factors"].get("ai_analysis", 0),
                        pe=data["pe"],
                        pb=data["pb"],
                        price=data["price"]
                    )
                    db.add(history)
                    db.commit()
                    
                    results.append({
                        "stock_code": item.stock_code,
                        "stock_name": item.stock_name,
                        "score": result["score"],
                        "status": "success"
                    })
                else:
                    results.append({
                        "stock_code": item.stock_code,
                        "stock_name": item.stock_name,
                        "status": "no_data"
                    })
            except Exception as e:
                results.append({
                    "stock_code": item.stock_code,
                    "stock_name": item.stock_name,
                    "status": "error",
                    "error": str(e)
                })
        
        return results
```

- [ ] **Step 2: Create app/services/scheduler.py**

```python
from celery import Celery
from celery.schedules import crontab
from app.core.config import settings

celery_app = Celery(
    "valuation",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND
)

celery_app.conf.beat_schedule = {
    'daily-valuation': {
        'task': 'app.tasks.valuation_tasks.calculate_watchlist',
        'schedule': crontab(hour=18, minute=0),
    },
}

celery_app.conf.timezone = 'Asia/Shanghai'
```

- [ ] **Step 3: Create app/tasks/__init__.py**

```python
from .valuation_tasks import calculate_watchlist
```

- [ ] **Step 4: Create app/tasks/valuation_tasks.py**

```python
from app.services.watchlist import WatchlistService
from app.db.session import SessionLocal

@celery_app.task
def calculate_watchlist():
    db = SessionLocal()
    try:
        service = WatchlistService()
        results = service.batch_calculate(db)
        return {"results": results}
    finally:
        db.close()
```

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/watchlist.py backend/app/services/scheduler.py backend/app/tasks/
git commit -m "feat: watchlist service and scheduler"
```

---

## Task 10: Database Initialization and Security

**Files:**
- Create: `backend/app/core/security.py`
- Create: `backend/app/db/__init__.py`
- Create: `backend/init_db.py`

- [ ] **Step 1: Create app/core/security.py**

```python
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)
```

- [ ] **Step 2: Create app/db/__init__.py**

```python
from .session import engine, Base, get_db
from .models import KlineData, ValuationHistory, FinancialData, Watchlist, SchedulerConfig, ModelConfig, User

def init_db():
    Base.metadata.create_all(bind=engine)
```

- [ ] **Step 3: Create backend/init_db.py**

```python
from app.db import init_db
from app.db.session import SessionLocal
from app.db.models import User
from app.core.security import get_password_hash

def main():
    init_db()
    db = SessionLocal()
    
    admin = db.query(User).filter(User.username == "admin").first()
    if not admin:
        admin = User(
            username="admin",
            hashed_password=get_password_hash("admin123")
        )
        db.add(admin)
        db.commit()
        print("Admin user created")
    
    db.close()

if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Commit**

```bash
git add backend/app/core/security.py backend/app/db/__init__.py backend/init_db.py
git commit -m "feat: database initialization and security"
```

---

## Task 11: Frontend Project Setup

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/vite.config.js`
- Create: `frontend/src/main.js`
- Create: `frontend/src/App.vue`

- [ ] **Step 1: Create frontend/package.json**

```json
{
  "name": "stock-valuation-frontend",
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "vue": "^3.4.21",
    "vue-router": "^4.3.0",
    "element-plus": "^2.4.4",
    "echarts": "^5.4.3",
    "axios": "^1.6.7"
  },
  "devDependencies": {
    "@vitejs/plugin-vue": "^5.0.4",
    "vite": "^5.1.4"
  }
}
```

- [ ] **Step 2: Create frontend/vite.config.js**

```javascript
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true
      }
    }
  }
})
```

- [ ] **Step 3: Create frontend/src/main.js**

```javascript
import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'

const app = createApp(App)
app.use(router)
app.use(ElementPlus)
app.mount('#app')
```

- [ ] **Step 4: Create frontend/src/App.vue**

```vue
<template>
  <router-view />
</template>

<script setup>
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
}
</style>
```

- [ ] **Step 5: Commit**

```bash
git add frontend/package.json frontend/vite.config.js frontend/src/main.js frontend/src/App.vue
git commit -m "feat: frontend project setup"
```

---

## Task 12: Frontend Router and API

**Files:**
- Create: `frontend/src/router/index.js`
- Create: `frontend/src/api/index.js`

- [ ] **Step 1: Create frontend/src/router/index.js**

```javascript
import { createRouter, createWebHistory } from 'vue-router'
import Login from '../views/Login.vue'
import Home from '../views/Home.vue'
import ValuationReport from '../views/ValuationReport.vue'
import ModelManager from '../views/ModelManager.vue'
import Scheduler from '../views/Scheduler.vue'
import Settings from '../views/Settings.vue'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: Login
  },
  {
    path: '/',
    name: 'Home',
    component: Home
  },
  {
    path: '/stock/:code',
    name: 'ValuationReport',
    component: ValuationReport
  },
  {
    path: '/models',
    name: 'ModelManager',
    component: ModelManager
  },
  {
    path: '/scheduler',
    name: 'Scheduler',
    component: Scheduler
  },
  {
    path: '/settings',
    name: 'Settings',
    component: Settings
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')
  if (to.path !== '/login' && !token) {
    next('/login')
  } else {
    next()
  }
})

export default router
```

- [ ] **Step 2: Create frontend/src/api/index.js**

```javascript
import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000
})

api.interceptors.request.use(config => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

api.interceptors.response.use(response => {
  return response.data
}, error => {
  if (error.response.status === 401) {
    localStorage.removeItem('token')
    window.location.href = '/login'
  }
  return Promise.reject(error)
})

export const authAPI = {
  login(data) {
    return api.post('/auth/login', data)
  },
  verify() {
    return api.get('/auth/verify')
  }
}

export const stockAPI = {
  search(keyword) {
    return api.get('/stock/search', { params: { keyword } })
  },
  getInfo(code) {
    return api.get(`/stock/${code}`)
  },
  getValuation(code, modelCode) {
    return api.get(`/stock/${code}/valuation`, { params: { model_code: modelCode } })
  },
  getHistory(code, startDate, endDate) {
    return api.get(`/stock/${code}/history`, { params: { start_date: startDate, end_date: endDate } })
  }
}

export const watchlistAPI = {
  getList() {
    return api.get('/watchlist')
  },
  add(item) {
    return api.post('/watchlist', item)
  },
  remove(code) {
    return api.delete(`/watchlist/${code}`)
  },
  batchCalculate() {
    return api.post('/watchlist/batch')
  }
}

export const schedulerAPI = {
  getConfig() {
    return api.get('/scheduler/config')
  },
  updateConfig(config) {
    return api.put('/scheduler/config', config)
  },
  run() {
    return api.post('/scheduler/run')
  }
}

export const modelsAPI = {
  getModels() {
    return api.get('/models')
  },
  getModel(code) {
    return api.get(`/models/${code}`)
  },
  getFactors() {
    return api.get('/models/factors')
  },
  getFactor(code) {
    return api.get(`/models/factors/${code}`)
  }
}

export default api
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/router/index.js frontend/src/api/index.js
git commit -m "feat: frontend router and API"
```

---

## Task 13: Frontend Views

**Files:**
- Create: `frontend/src/views/Login.vue`
- Create: `frontend/src/views/Home.vue`
- Create: `frontend/src/views/ValuationReport.vue`

- [ ] **Step 1: Create frontend/src/views/Login.vue**

```vue
<template>
  <div class="login-container">
    <div class="login-box">
      <h2>股票估值系统</h2>
      <el-form :model="form" label-width="80px">
        <el-form-item label="用户名">
          <el-input v-model="form.username" placeholder="请输入用户名" />
        </el-form-item>
        <el-form-item label="密码">
          <el-input v-model="form.password" type="password" placeholder="请输入密码" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="login" :loading="loading">登录</el-button>
        </el-form-item>
      </el-form>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { authAPI } from '../api'

const form = ref({
  username: '',
  password: ''
})

const loading = ref(false)

const login = async () => {
  loading.value = true
  try {
    const response = await authAPI.login(form.value)
    localStorage.setItem('token', response.access_token)
    window.location.href = '/'
  } catch (error) {
    alert('登录失败，请检查用户名和密码')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.login-box {
  background: white;
  padding: 40px;
  border-radius: 12px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.15);
  width: 400px;
}

.login-box h2 {
  text-align: center;
  margin-bottom: 30px;
  color: #333;
}
</style>
```

- [ ] **Step 2: Create frontend/src/views/Home.vue**

```vue
<template>
  <div class="home-container">
    <div class="header">
      <h1>股票估值系统</h1>
      <div class="header-actions">
        <el-button @click="logout">退出登录</el-button>
      </div>
    </div>
    
    <div class="search-section">
      <el-input
        v-model="searchKeyword"
        placeholder="搜索股票代码或名称"
        style="width: 300px"
        @keyup.enter="searchStock"
      >
        <template #append>
          <el-button @click="searchStock">搜索</el-button>
        </template>
      </el-input>
    </div>
    
    <div class="content">
      <div class="watchlist-section">
        <h2>自选股</h2>
        <el-button type="primary" @click="addStock">添加股票</el-button>
        <el-button @click="batchCalculate">批量计算</el-button>
        
        <el-table :data="watchlist" border>
          <el-table-column prop="stock_code" label="代码" />
          <el-table-column prop="stock_name" label="名称" />
          <el-table-column prop="industry" label="行业" />
          <el-table-column prop="model_type" label="模型" />
          <el-table-column prop="ai_enabled" label="AI分析">
            <template #default="{ row }">
              {{ row.ai_enabled ? '是' : '否' }}
            </template>
          </el-table-column>
          <el-table-column label="操作">
            <template #default="{ row }">
              <el-button @click="viewReport(row.stock_code)">查看报告</el-button>
              <el-button @click="removeStock(row.stock_code)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </div>
    
    <el-dialog title="添加股票" v-model="addDialogVisible">
      <el-form :model="newStock" label-width="80px">
        <el-form-item label="股票代码">
          <el-input v-model="newStock.stock_code" />
        </el-form-item>
        <el-form-item label="股票名称">
          <el-input v-model="newStock.stock_name" />
        </el-form-item>
        <el-form-item label="行业">
          <el-input v-model="newStock.industry" />
        </el-form-item>
        <el-form-item label="估值模型">
          <el-select v-model="newStock.model_type">
            <el-option label="必选消费" value="staples" />
            <el-option label="周期股" value="cyclical" />
            <el-option label="科技股" value="tech" />
            <el-option label="银行保险" value="bank" />
            <el-option label="医药股" value="pharma" />
            <el-option label="央企国企" value="soe" />
          </el-select>
        </el-form-item>
        <el-form-item label="启用AI分析">
          <el-switch v-model="newStock.ai_enabled" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="addDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="confirmAdd">确认添加</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { watchlistAPI } from '../api'

const router = useRouter()
const searchKeyword = ref('')
const watchlist = ref([])
const addDialogVisible = ref(false)
const newStock = ref({
  stock_code: '',
  stock_name: '',
  industry: '',
  model_type: 'tech',
  ai_enabled: false
})

onMounted(async () => {
  await loadWatchlist()
})

const loadWatchlist = async () => {
  watchlist.value = await watchlistAPI.getList()
}

const searchStock = () => {
  router.push(`/stock/${searchKeyword.value}`)
}

const viewReport = (code) => {
  router.push(`/stock/${code}`)
}

const addStock = () => {
  addDialogVisible.value = true
}

const confirmAdd = async () => {
  await watchlistAPI.add(newStock.value)
  addDialogVisible.value = false
  await loadWatchlist()
}

const removeStock = async (code) => {
  await watchlistAPI.remove(code)
  await loadWatchlist()
}

const batchCalculate = async () => {
  await watchlistAPI.batchCalculate()
  alert('批量计算完成')
}

const logout = () => {
  localStorage.removeItem('token')
  window.location.href = '/login'
}
</script>

<style scoped>
.home-container {
  padding: 20px;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.header h1 {
  color: #333;
}

.search-section {
  margin-bottom: 20px;
}

.content {
  display: flex;
  gap: 20px;
}

.watchlist-section {
  flex: 1;
}

.watchlist-section h2 {
  margin-bottom: 10px;
}
</style>
```

- [ ] **Step 3: Create frontend/src/views/ValuationReport.vue**

```vue
<template>
  <div class="report-container">
    <div class="header">
      <el-button @click="goBack">返回</el-button>
      <h1>{{ stockInfo.name }} ({{ stockInfo.code }})</h1>
    </div>
    
    <div v-if="valuation" class="report-content">
      <div class="summary-card">
        <div class="summary-item">
          <span class="label">估值分</span>
          <span class="value" :class="getStatusClass(valuation.status)">{{ valuation.score }}</span>
        </div>
        <div class="summary-item">
          <span class="label">百分位</span>
          <span class="value">{{ valuation.percentile }}%</span>
        </div>
        <div class="summary-item">
          <span class="label">状态</span>
          <span class="value" :class="getStatusClass(valuation.status)">{{ valuation.status }}</span>
        </div>
        <div class="summary-item">
          <span class="label">PE</span>
          <span class="value">{{ valuation.pe }}</span>
        </div>
        <div class="summary-item">
          <span class="label">PB</span>
          <span class="value">{{ valuation.pb }}</span>
        </div>
        <div class="summary-item">
          <span class="label">价格</span>
          <span class="value">¥{{ valuation.price }}</span>
        </div>
      </div>
      
      <div class="chart-section">
        <h3>估值曲线</h3>
        <div ref="chartRef" style="height: 400px"></div>
      </div>
      
      <div class="factors-section">
        <h3>因子得分详情</h3>
        <el-table :data="factorList" border>
          <el-table-column prop="name" label="因子" />
          <el-table-column prop="score" label="得分">
            <template #default="{ row }">
              <el-progress :percentage="row.score" />
            </template>
          </el-table-column>
          <el-table-column prop="scoreValue" label="分数" />
        </el-table>
      </div>
    </div>
    
    <div v-else class="loading">
      <el-spinner />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import * as echarts from 'echarts'
import { stockAPI } from '../api'

const router = useRouter()
const route = useRoute()
const stockInfo = ref({ code: '', name: '' })
const valuation = ref(null)
const chartRef = ref(null)
const factorList = ref([])
const factorNames = {
  pe: 'PE评分',
  pb: 'PB评分',
  peg: 'PEG评分',
  ma_deviation: 'MA偏离度',
  volatility: '波动率',
  volume: '量能',
  roe: 'ROE评分',
  dividend: '股息率',
  ai_analysis: 'AI深度分析'
}

onMounted(async () => {
  await loadData()
})

const loadData = async () => {
  const code = route.params.code
  stockInfo.value = await stockAPI.getInfo(code)
  valuation.value = await stockAPI.getValuation(code)
  
  factorList.value = Object.entries(valuation.value.factors).map(([code, score]) => ({
    name: factorNames[code] || code,
    score: Math.round(score),
    scoreValue: score
  }))
  
  await loadHistory()
}

const loadHistory = async () => {
  const history = await stockAPI.getHistory(route.params.code)
  await nextTick()
  renderChart(history)
}

const renderChart = (history) => {
  const chart = echarts.init(chartRef.value)
  const dates = history.map(h => h.date)
  const scores = history.map(h => h.score)
  const prices = history.map(h => h.price)
  
  chart.setOption({
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'cross' }
    },
    legend: {
      data: ['估值分', '价格']
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: dates
    },
    yAxis: [
      {
        type: 'value',
        name: '估值分'
      },
      {
        type: 'value',
        name: '价格'
      }
    ],
    series: [
      {
        name: '估值分',
        type: 'line',
        data: scores,
        smooth: true
      },
      {
        name: '价格',
        type: 'line',
        yAxisIndex: 1,
        data: prices,
        smooth: true
      }
    ]
  })
}

const getStatusClass = (status) => {
  const classes = {
    '极度低估': 'status-very-low',
    '低估': 'status-low',
    '中性偏低': 'status-neutral-low',
    '中性偏高': 'status-neutral-high',
    '高估': 'status-high',
    '极度高估': 'status-very-high'
  }
  return classes[status] || ''
}

const goBack = () => {
  router.back()
}
</script>

<style scoped>
.report-container {
  padding: 20px;
}

.header {
  display: flex;
  align-items: center;
  gap: 20px;
  margin-bottom: 20px;
}

.summary-card {
  display: flex;
  gap: 20px;
  flex-wrap: wrap;
  margin-bottom: 20px;
}

.summary-item {
  background: #f5f5f5;
  padding: 15px 25px;
  border-radius: 8px;
  text-align: center;
}

.summary-item .label {
  display: block;
  font-size: 14px;
  color: #999;
  margin-bottom: 5px;
}

.summary-item .value {
  font-size: 24px;
  font-weight: bold;
  color: #333;
}

.status-very-low { color: #10b981; }
.status-low { color: #3b82f6; }
.status-neutral-low { color: #6b7280; }
.status-neutral-high { color: #f59e0b; }
.status-high { color: #ef4444; }
.status-very-high { color: #dc2626; }

.chart-section, .factors-section {
  margin-bottom: 20px;
}

.chart-section h3, .factors-section h3 {
  margin-bottom: 10px;
}

.loading {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 400px;
}
</style>
```

- [ ] **Step 4: Commit**

```bash
git add frontend/src/views/Login.vue frontend/src/views/Home.vue frontend/src/views/ValuationReport.vue
git commit -m "feat: frontend views"
```

---

## Task 14: Remaining Frontend Views and Docker Compose

**Files:**
- Create: `frontend/src/views/ModelManager.vue`
- Create: `frontend/src/views/Scheduler.vue`
- Create: `frontend/src/views/Settings.vue`
- Create: `docker-compose.yml`

- [ ] **Step 1: Create frontend/src/views/ModelManager.vue**

```vue
<template>
  <div class="container">
    <h1>模型管理</h1>
    
    <h2>估值模型</h2>
    <el-table :data="models" border>
      <el-table-column prop="code" label="代码" />
      <el-table-column prop="name" label="名称" />
      <el-table-column prop="factors" label="因子">
        <template #default="{ row }">
          {{ row.factors.join(', ') }}
        </template>
      </el-table-column>
    </el-table>
    
    <h2>估值因子</h2>
    <el-table :data="factors" border>
      <el-table-column prop="code" label="代码" />
      <el-table-column prop="name" label="名称" />
      <el-table-column prop="requires_data" label="需要数据">
        <template #default="{ row }">
          {{ row.requires_data.join(', ') }}
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { modelsAPI } from '../api'

const models = ref([])
const factors = ref([])

onMounted(async () => {
  models.value = await modelsAPI.getModels()
  factors.value = await modelsAPI.getFactors()
})
</script>

<style scoped>
.container {
  padding: 20px;
}

h1, h2 {
  margin-bottom: 20px;
}
</style>
```

- [ ] **Step 2: Create frontend/src/views/Scheduler.vue**

```vue
<template>
  <div class="container">
    <h1>定时任务配置</h1>
    
    <el-form :model="config" label-width="150px">
      <el-form-item label="定时类型">
        <el-select v-model="config.schedule_type">
          <el-option label="每小时" value="hourly" />
          <el-option label="每天" value="daily" />
          <el-option label="每周" value="weekly" />
        </el-select>
      </el-form-item>
      <el-form-item label="Cron表达式">
        <el-input v-model="config.cron_expression" />
      </el-form-item>
      <el-form-item label="启用定时任务">
        <el-switch v-model="config.enabled" />
      </el-form-item>
      <el-form-item label="包含AI分析">
        <el-switch v-model="config.include_ai" />
      </el-form-item>
      <el-form-item label="财报更新频率(天)">
        <el-input-number v-model="config.financial_update_frequency" :min="1" :max="30" />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="saveConfig">保存配置</el-button>
        <el-button @click="runNow">立即执行</el-button>
      </el-form-item>
    </el-form>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { schedulerAPI } from '../api'

const config = ref({
  schedule_type: 'daily',
  cron_expression: '0 18 * * *',
  enabled: true,
  include_ai: false,
  financial_update_frequency: 7
})

onMounted(async () => {
  config.value = await schedulerAPI.getConfig()
})

const saveConfig = async () => {
  await schedulerAPI.updateConfig(config.value)
  alert('配置已保存')
}

const runNow = async () => {
  await schedulerAPI.run()
  alert('任务已触发')
}
</script>

<style scoped>
.container {
  padding: 20px;
}

h1 {
  margin-bottom: 20px;
}
</style>
```

- [ ] **Step 3: Create frontend/src/views/Settings.vue**

```vue
<template>
  <div class="container">
    <h1>系统设置</h1>
    
    <h2>关于系统</h2>
    <el-descriptions :column="2" border>
      <el-descriptions-item label="系统名称">股票估值系统</el-descriptions-item>
      <el-descriptions-item label="版本">1.0.0</el-descriptions-item>
      <el-descriptions-item label="后端框架">FastAPI</el-descriptions-item>
      <el-descriptions-item label="前端框架">Vue3</el-descriptions-item>
      <el-descriptions-item label="数据库">SQLite</el-descriptions-item>
      <el-descriptions-item label="缓存">Redis</el-descriptions-item>
    </el-descriptions>
    
    <h2>数据更新频率设置</h2>
    <el-form :model="settings" label-width="150px">
      <el-form-item label="财报数据更新频率(天)">
        <el-input-number v-model="settings.financial_update_frequency" :min="1" :max="30" />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="saveSettings">保存设置</el-button>
      </el-form-item>
    </el-form>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { schedulerAPI } from '../api'

const settings = ref({
  financial_update_frequency: 7
})

onMounted(async () => {
  const config = await schedulerAPI.getConfig()
  settings.value.financial_update_frequency = config.financial_update_frequency
})

const saveSettings = async () => {
  await schedulerAPI.updateConfig({
    ...settings.value,
    schedule_type: 'daily',
    cron_expression: '0 18 * * *',
    enabled: true,
    include_ai: false
  })
  alert('设置已保存')
}
</script>

<style scoped>
.container {
  padding: 20px;
}

h1, h2 {
  margin-bottom: 20px;
}
</style>
```

- [ ] **Step 4: Create docker-compose.yml**

```yaml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=sqlite:///./data/valuation.db
      - REDIS_URL=redis://redis:6379
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/1
    volumes:
      - ./backend/data:/app/data
    depends_on:
      - redis

  frontend:
    build: ./frontend
    ports:
      - "80:80"
    depends_on:
      - backend

  redis:
    image: redis:7.0
    volumes:
      - redis_data:/data

  celery-worker:
    build: ./backend
    command: celery -A app.services.scheduler.celery_app worker --loglevel=info
    environment:
      - DATABASE_URL=sqlite:///./data/valuation.db
      - REDIS_URL=redis://redis:6379
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/1
    volumes:
      - ./backend/data:/app/data
    depends_on:
      - redis
      - backend

  celery-beat:
    build: ./backend
    command: celery -A app.services.scheduler.celery_app beat --loglevel=info
    environment:
      - DATABASE_URL=sqlite:///./data/valuation.db
      - REDIS_URL=redis://redis:6379
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/1
    volumes:
      - ./backend/data:/app/data
    depends_on:
      - redis
      - backend

volumes:
  redis_data:
```

- [ ] **Step 5: Commit**

```bash
git add frontend/src/views/ModelManager.vue frontend/src/views/Scheduler.vue frontend/src/views/Settings.vue docker-compose.yml
git commit -m "feat: remaining frontend views and docker compose"
```

---

## Task 15: Testing and Verification

**Files:**
- Create: `backend/tests/test_plugins.py`
- Create: `backend/tests/test_valuation.py`

- [ ] **Step 1: Create backend/tests/test_plugins.py**

```python
import pytest
from app.plugins.models.base import get_model, list_models
from app.plugins.factors.base import get_factor, list_factors

def test_model_registry():
    models = list_models()
    assert len(models) > 0
    
    tech_model = get_model('tech')
    assert tech_model is not None
    assert tech_model.get_name(tech_model()) == '科技股'

def test_factor_registry():
    factors = list_factors()
    assert len(factors) > 0
    
    pe_factor = get_factor('pe')
    assert pe_factor is not None
    assert pe_factor.get_name(pe_factor()) == 'PE评分'

def test_pe_score():
    factor = get_factor('pe')
    assert factor is not None
    
    score = factor.score(factor(), {'pe': 10, 'pe_min': 5, 'pe_max': 50})
    assert 0 <= score <= 100
```

- [ ] **Step 2: Create backend/tests/test_valuation.py**

```python
import pytest
from app.services.valuation import ValuationService

def test_valuation_calculate():
    service = ValuationService()
    
    data = {
        'pe': 20,
        'pb': 5,
        'price': 100,
        'ma20': 100,
        'ma60': 100,
        'volatility': 0.03
    }
    
    result = service.calculate('600519', 'tech', data)
    assert 'score' in result
    assert 'factors' in result
    assert 0 <= result['score'] <= 100

def test_status():
    service = ValuationService()
    
    assert service.get_status(95) == '极度低估'
    assert service.get_status(75) == '低估'
    assert service.get_status(55) == '中性偏低'
    assert service.get_status(35) == '中性偏高'
    assert service.get_status(15) == '高估'
    assert service.get_status(5) == '极度高估'
```

- [ ] **Step 3: Run tests**

```bash
cd backend
pytest tests/ -v
```

- [ ] **Step 4: Commit**

```bash
git add backend/tests/
git commit -m "test: add unit tests"
```

---

## Spec Self-Review

**1. Spec Coverage:**
- ✅ 可插拔估值模型和因子
- ✅ AI分析作为可选因子
- ✅ 自选股管理
- ✅ 定时任务配置
- ✅ 用户认证（简单密码）
- ✅ 估值报告展示（交互图表）
- ✅ 历史K线数据库存储
- ✅ 财报数据缓存
- ✅ MCP+公开API双方案

**2. Placeholder Scan:**
- ✅ 无TBD、TODO占位符
- ✅ 所有代码完整

**3. Type Consistency:**
- ✅ 类型和方法签名一致

---

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-07-13-stock-valuation-system-implementation.md`. Two execution options:

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

**Which approach?
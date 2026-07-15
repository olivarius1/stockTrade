# Docker开发模式、缓存策略重构与注释规范 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 创建 Docker 开发模式挂载、重构缓存策略（移除实时/DB缓存，新增计算结果缓存）、为核心模块补齐 Google-style/JSDoc 注释。

**Architecture:** 通过 docker-compose.override.yml 实现开发模式源码挂载 + uvicorn --reload；移除 data_service 中 K线/财务的 Redis 缓存，改为仅缓存 calculate_ma/calculate_volatility 的计算结果；为 API层、Service层、核心配置、前端核心文件补齐 ADR 式注释。

**Tech Stack:** Docker Compose, FastAPI, Redis, Vue 3, Vite

---

## File Structure

| 文件 | 操作 | 职责 |
|------|------|------|
| `docker-compose.override.yml` | 新建 | 开发模式源码挂载 + hot reload |
| `backend/app/services/data_service.py` | 修改 | 移除K线/财务缓存，新增MA/波动率缓存，补齐注释 |
| `backend/app/tasks/valuation_tasks.py` | 修改 | K线更新后清除计算缓存，补齐注释 |
| `backend/app/services/valuation.py` | 修改 | 补齐 Google-style 注释 |
| `backend/app/services/watchlist.py` | 修改 | 补齐 Google-style 注释 |
| `backend/app/api/stock.py` | 修改 | 补齐端点 docstring |
| `backend/app/api/valuation.py` | 修改 | 补齐端点 docstring |
| `backend/app/api/watchlist.py` | 修改 | 补齐端点 docstring |
| `backend/app/core/cache.py` | 修改 | 补齐模块 docstring + cache_clear_pattern 函数 |
| `backend/app/core/config.py` | 修改 | 补齐模块 docstring |
| `backend/app/db/models.py` | 修改 | 补齐表级注释 |
| `frontend/src/api/index.js` | 修改 | 补齐 JSDoc 注释 |
| `frontend/src/views/ValuationReport.vue` | 修改 | 补齐模块注释 |
| `frontend/src/views/Home.vue` | 修改 | 补齐模块注释 |

---

### Task 1: 创建 docker-compose.override.yml

**Files:**
- Create: `docker-compose.override.yml`

- [ ] **Step 1: 创建 override 文件**

```yaml
# 开发环境覆盖配置，docker-compose up 自动合并此文件。
# 生产部署用: docker-compose -f docker-compose.yml up -d
services:
  backend:
    volumes:
      - ./backend/app:/app/app
      - ./backend/scripts:/app/scripts
      - ./backend/entrypoint.sh:/app/entrypoint.sh
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
    environment:
      - DEBUG=true

  celery-worker:
    volumes:
      - ./backend/app:/app/app
      - ./backend/scripts:/app/scripts

  celery-beat:
    volumes:
      - ./backend/app:/app/app
```

- [ ] **Step 2: 验证开发模式启动**

Run: `cd /Users/zhanghe/MyProjs/trade/eval_sys/stockTrade && docker-compose down && docker-compose up -d`
Expected: backend 容器以 uvicorn --reload 启动，修改 Python 文件后自动重载

- [ ] **Step 3: 验证 hot reload 生效**

Run: `docker-compose logs --tail=5 backend`
Expected: 看到 `Uvicorn running on http://0.0.0.0:8000` 和 `Application startup complete`

- [ ] **Step 4: 提交**

```bash
git add docker-compose.override.yml
git commit -m "feat: add docker-compose.override.yml for development hot-reload"
```

---

### Task 2: 移除 K线数据和财务数据的 Redis 缓存

**Files:**
- Modify: `backend/app/services/data_service.py`

- [ ] **Step 1: 重写 get_kline_data 移除缓存逻辑**

将 `get_kline_data` 方法替换为以下内容（移除所有 cache_get/cache_set/cache_delete 调用，保留 JSON 序列化函数因为 calculate_ma 会用到）:

```python
    def get_kline_data(self, stock_code: str, start_date: date = None, end_date: date = None, db=None) -> List[Dict]:
        """获取股票K线数据，合并实时行情和历史数据。

        为什么不缓存：股票价格实时变动，缓存会导致估值基于过期价格。
        历史数据从DB查询，SQLAlchemy连接池已做优化，无需额外缓存。

        Args:
            stock_code: 股票代码，如 "600519"
            start_date: 开始日期，默认近10年
            end_date: 结束日期，默认今天
            db: 数据库会话

        Returns:
            列表，第一个元素是实时行情，后续是历史K线数据。
            失败时返回空列表。
        """
        if start_date is None:
            start_date = date.today() - timedelta(days=3650)
        if end_date is None:
            end_date = date.today()

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

            return result

        except Exception as e:
            logger.error(f"Failed to get kline data for {stock_code}: {e}")
            return []
```

- [ ] **Step 2: 重写 get_financial_data 移除缓存逻辑**

```python
    def get_financial_data(self, stock_code: str, db=None) -> Dict:
        """获取最新财务数据。

        为什么不缓存：财务数据更新频率用户可配置，缓存可能导致决策基于过期数据。
        SQLAlchemy连接池已优化DB查询，单用户场景QPS极低。

        Args:
            stock_code: 股票代码
            db: 数据库会话

        Returns:
            包含 eps, revenue, net_profit, roe, gross_margin, dividend_rate 的字典。
            无数据时返回空字典。
        """
        if db:
            latest = db.query(FinancialData).filter(
                FinancialData.stock_code == stock_code
            ).order_by(FinancialData.report_date.desc()).first()

            if latest:
                return {
                    "eps": latest.eps,
                    "revenue": latest.revenue,
                    "net_profit": latest.net_profit,
                    "roe": latest.roe,
                    "gross_margin": latest.gross_margin,
                    "dividend_rate": latest.dividend_rate
                }

        return {}
```

- [ ] **Step 3: 清理不再需要的 import**

将文件顶部的 import 行中移除 `cache_get, cache_set, cache_delete`（Task 3 会重新引入 `cache_get, cache_set, cache_delete` 用于计算缓存）:

```python
import requests
import json
import logging
from typing import Dict, List
from datetime import date, timedelta, datetime
from app.db.models import KlineData, FinancialData
```

暂时不引入 cache，Task 3 会加回来。

- [ ] **Step 4: 验证服务正常**

Run: `docker-compose restart backend && sleep 3 && docker-compose exec -T backend python3 -c "import requests; r = requests.get('http://localhost:8000/api/stock/600519'); print(r.status_code, r.text[:100])"`
Expected: `200 {"code":"600519","name":"贵州茅台"...`

- [ ] **Step 5: 提交**

```bash
git add backend/app/services/data_service.py
git commit -m "refactor: remove Redis caching for kline and financial data"
```

---

### Task 3: 为 calculate_ma 和 calculate_volatility 添加计算结果缓存

**Files:**
- Modify: `backend/app/services/data_service.py`
- Modify: `backend/app/core/cache.py`

- [ ] **Step 1: 在 cache.py 添加 cache_clear_pattern 函数**

在 `cache_delete` 函数后面添加:

```python
def cache_clear_pattern(pattern: str):
    """清除匹配模式的所有缓存键。

    用于K线数据更新后清除衍生计算缓存（MA、波动率等）。
    """
    if _redis_available:
        try:
            keys = redis_client.keys(pattern)
            if keys:
                redis_client.delete(*keys)
            return
        except Exception as e:
            logger.warning(f"Redis clear pattern failed: {e}")
    # 内存缓存不支持模式匹配，逐个检查
    keys_to_delete = [k for k in _memory_cache if pattern.replace("*", "") in k]
    for k in keys_to_delete:
        _memory_cache.pop(k, None)
```

- [ ] **Step 2: 在 data_service.py 顶部恢复 cache import**

```python
import requests
import json
import logging
from typing import Dict, List
from datetime import date, timedelta, datetime
from app.db.models import KlineData, FinancialData
from app.core.cache import cache_get, cache_set, cache_clear_pattern
```

- [ ] **Step 3: 重写 calculate_ma 添加缓存**

```python
    def calculate_ma(self, stock_code: str, prices: List[float], period: int = 20) -> float:
        """计算移动平均线。

        为什么缓存：MA计算需要遍历价格序列，批量计算47只股票时开销显著。
        K线数据是append-only的，用 len(prices) 作为数据版本标识，
        数据不变时结果恒定，数据新增时长度变化自动失效缓存。

        Args:
            stock_code: 股票代码，用于缓存键
            prices: 收盘价列表
            period: 均线周期，默认20日

        Returns:
            移动平均值。数据不足时返回0。
        """
        if len(prices) < period:
            return 0

        cache_key = f"calc:ma:{stock_code}:{period}:{len(prices)}"
        cached = cache_get(cache_key)
        if cached is not None:
            try:
                return float(cached)
            except (ValueError, TypeError):
                pass

        result = sum(prices[-period:]) / period
        cache_set(cache_key, str(result), 3600)
        return result
```

- [ ] **Step 4: 重写 calculate_volatility 添加缓存**

```python
    def calculate_volatility(self, stock_code: str, prices: List[float]) -> float:
        """计算价格波动率（日收益率标准差）。

        为什么缓存：波动率计算需要遍历全部价格序列两次，计算量大于MA。
        同理用 len(prices) 作为数据版本标识。

        Args:
            stock_code: 股票代码，用于缓存键
            prices: 收盘价列表

        Returns:
            波动率。数据不足时返回0。
        """
        if len(prices) < 2:
            return 0

        cache_key = f"calc:volatility:{stock_code}:{len(prices)}"
        cached = cache_get(cache_key)
        if cached is not None:
            try:
                return float(cached)
            except (ValueError, TypeError):
                pass

        returns = []
        for i in range(1, len(prices)):
            returns.append((prices[i] - prices[i-1]) / prices[i-1])
        if not returns:
            return 0
        mean = sum(returns) / len(returns)
        variance = sum((r - mean) ** 2 for r in returns) / len(returns)
        result = variance ** 0.5

        cache_set(cache_key, str(result), 3600)
        return result
```

- [ ] **Step 5: 更新所有调用方传入 stock_code**

需要修改以下文件中所有 `calculate_ma` 和 `calculate_volatility` 的调用：

**`backend/app/api/stock.py`** 第57-59行:
```python
    ma20 = data_service.calculate_ma(code, prices, period=20)
    ma60 = data_service.calculate_ma(code, prices, period=60)
    volatility = data_service.calculate_volatility(code, prices)
```

**`backend/app/api/valuation.py`** 第31-33行:
```python
    ma20 = data_service.calculate_ma(code, prices, period=20)
    ma60 = data_service.calculate_ma(code, prices, period=60)
    volatility = data_service.calculate_volatility(code, prices)
```

**`backend/app/api/watchlist.py`** 第35-37行:
```python
            ma20 = data_service.calculate_ma(item.stock_code, prices, period=20)
            ma60 = data_service.calculate_ma(item.stock_code, prices, period=60)
            volatility = data_service.calculate_volatility(item.stock_code, prices)
```

**`backend/app/services/watchlist.py`** 第88-90行:
```python
                ma20 = self.data_service.calculate_ma(stock_code, closes, period=20)
                ma60 = self.data_service.calculate_ma(stock_code, closes, period=60)
                volatility = self.data_service.calculate_volatility(stock_code, closes)
```

**`backend/app/tasks/valuation_tasks.py`** 第47-49行:
```python
                        ma20 = service.data_service.calculate_ma(stock_code, closes, period=20)
                        ma60 = service.data_service.calculate_ma(stock_code, closes, period=60)
                        volatility = service.data_service.calculate_volatility(stock_code, closes)
```

- [ ] **Step 6: 验证服务正常**

Run: `docker-compose restart backend && sleep 3 && docker-compose exec -T backend python3 -c "import requests; r = requests.get('http://localhost:8000/api/valuation/report/600519'); print(r.status_code, r.text[:200])"`
Expected: `200 {"stock_code":"600519"...`

- [ ] **Step 7: 提交**

```bash
git add backend/app/core/cache.py backend/app/services/data_service.py backend/app/api/stock.py backend/app/api/valuation.py backend/app/api/watchlist.py backend/app/services/watchlist.py backend/app/tasks/valuation_tasks.py
git commit -m "feat: add computation result caching for MA and volatility"
```

---

### Task 4: 在 K线更新任务中添加缓存失效

**Files:**
- Modify: `backend/app/tasks/valuation_tasks.py`

- [ ] **Step 1: 在 update_kline_and_recalculate 中添加缓存清除**

在 `valuation_tasks.py` 文件顶部添加 import:

```python
from app.services.scheduler import celery_app
from app.services.watchlist import WatchlistService
from app.db.session import SessionLocal
from app.db.models import Watchlist, KlineData, ValuationHistory
from app.data.kline_manager import update_kline
from app.core.cache import cache_clear_pattern
```

在 `update_kline_and_recalculate` 函数中，`if added > 0:` 块的开头（第33行之后）添加:

```python
                if added > 0:
                    # K线数据更新后清除该股票的衍生计算缓存（MA、波动率等），
                    # 避免下次计算使用过期结果
                    cache_clear_pattern(f"calc:*:{stock_code}:*")
```

- [ ] **Step 2: 验证任务能正常执行**

Run: `docker-compose restart celery-worker && sleep 3 && docker-compose logs --tail=5 celery-worker`
Expected: 无导入错误，worker 正常启动

- [ ] **Step 3: 提交**

```bash
git add backend/app/tasks/valuation_tasks.py
git commit -m "feat: clear computation cache when kline data is updated"
```

---

### Task 5: 为 data_service.py 补齐完整注释

**Files:**
- Modify: `backend/app/services/data_service.py`

- [ ] **Step 1: 添加模块级 docstring 和类 docstring**

在文件顶部添加模块 docstring:

```python
"""数据服务模块，提供股票K线数据和财务数据的获取与计算。

为什么使用单独的 DataService 类而非直接在 API 中调用：
将数据获取逻辑与 API 路由解耦，便于在 Celery 定时任务和 API 中复用。

缓存策略说明：
- 实时行情和DB数据不缓存（保证数据一致性）
- 仅缓存计算量大的衍生数据（MA、波动率），用 len(prices) 作为数据版本标识
- K线数据更新时通过 cache_clear_pattern 清除衍生缓存
"""
```

为 `DataService` 类添加 docstring:

```python
class DataService:
    """股票数据服务，封装行情获取、历史数据查询和技术指标计算。"""
```

为 `search_stock` 和 `get_current_date` 添加注释:

```python
    def search_stock(self, keyword: str) -> List[Dict]:
        """搜索股票（当前为占位实现，后续接入搜索API）。"""
        return []
```

```python
    def get_current_date(self) -> date:
        """返回当前日期，用于估值评分记录。"""
        return date.today()
```

- [ ] **Step 2: 为 _json_serializer 和 _json_deserializer 添加注释**

```python
def _json_serializer(obj):
    """JSON 序列化辅助函数，处理 date/datetime 对象。

    为什么用 JSON 而非 eval：eval 不安全且无法处理日期对象，
    JSON 是标准序列化方式，通过 default 回调处理特殊类型。
    """
    if isinstance(obj, (date, datetime)):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")


def _json_deserializer(dct):
    """JSON 反序列化辅助函数，将 ISO 格式日期字符串还原为 date 对象。"""
    for key, val in dct.items():
        if isinstance(val, str):
            try:
                dct[key] = date.fromisoformat(val)
            except (ValueError, TypeError):
                pass
    return dct
```

- [ ] **Step 3: 提交**

```bash
git add backend/app/services/data_service.py
git commit -m "docs: add Google-style docstrings to data_service.py"
```

---

### Task 6: 为 valuation.py 和 watchlist.py (Service层) 补齐注释

**Files:**
- Modify: `backend/app/services/valuation.py`
- Modify: `backend/app/services/watchlist.py`

- [ ] **Step 1: 为 valuation.py 补齐注释**

在文件顶部添加模块 docstring:

```python
"""估值计算服务，协调估值模型和因子插件计算股票估值评分。

为什么用插件化设计：不同行业股票适用不同估值模型（如银行用PB，科技股用PE），
插件化允许灵活添加新模型和因子，无需修改核心逻辑。
"""
```

为 `ValuationService` 类和各方法添加 docstring:

```python
class ValuationService:
    """估值服务，通过模型插件和因子插件计算综合估值评分。"""

    def calculate(self, stock_code: str, model_code: str, data: Dict, ai_enabled: bool = False) -> Dict:
        """计算股票估值评分。

        流程：加载模型 → 获取因子列表和权重 → 逐个计算因子得分 → 加权汇总。
        AI因子可选，启用时占10%权重并重新归一化。

        Args:
            stock_code: 股票代码
            model_code: 估值模型代码（如 tech, bank, pharma）
            data: 因子计算所需数据（价格、PE、PB、MA等）
            ai_enabled: 是否启用AI分析因子

        Returns:
            包含 score, factors, weights, params 的字典。

        Raises:
            ValueError: 模型代码不存在时抛出。
        """
```

```python
    def calculate_percentile(self, stock_code: str, score: float, db) -> float:
        """计算当前评分在历史评分中的百分位。

        百分位越高表示当前估值越低（评分越高=越低估）。

        Args:
            stock_code: 股票代码
            score: 当前估值评分
            db: 数据库会话

        Returns:
            百分位（0-100）。无历史数据时返回50.0（中性）。
        """
```

```python
    def get_status(self, percentile: float) -> str:
        """根据百分位返回估值状态文本。

        百分位越高=越低估，越低=越高估。
        """
```

```python
    def get_models(self) -> List[Dict]:
        """列出所有可用的估值模型。"""
        return list_models()

    def get_factors(self) -> List[Dict]:
        """列出所有可用的估值因子。"""
        return list_factors()
```

- [ ] **Step 2: 为 watchlist.py (Service) 补齐注释**

在文件顶部添加模块 docstring:

```python
"""自选股管理服务，提供自选股的增删查和批量估值计算。

批量计算在 Celery 定时任务和 API 中复用，确保逻辑一致。
"""
```

为 `WatchlistService` 类和各方法添加 docstring:

```python
class WatchlistService:
    """自选股服务，管理自选股列表并触发估值计算。"""

    def __init__(self):
        self.valuation_service = ValuationService()
        self.data_service = DataService()

    def get_watchlist(self, db) -> List[Dict]:
        """获取全部自选股列表。"""

    def add_stock(self, db, stock_code: str, stock_name: str, industry: str, model_type: str, ai_enabled: bool = False):
        """添加股票到自选。

        Raises:
            ValueError: 股票已在自选列表中。
        """

    def remove_stock(self, db, stock_code: str):
        """从自选列表删除股票。

        Raises:
            ValueError: 股票不在自选列表中。
        """

    def batch_calculate(self, db) -> List[Dict]:
        """批量计算所有自选股的估值评分并写入历史记录。

        为什么每次都写DB：估值评分需要历史趋势分析，DB持久化支持回测和百分位计算。

        Returns:
            每只股票的计算结果列表，包含 score 和 status。
        """
```

- [ ] **Step 3: 提交**

```bash
git add backend/app/services/valuation.py backend/app/services/watchlist.py
git commit -m "docs: add Google-style docstrings to valuation and watchlist services"
```

---

### Task 7: 为 API 层补齐端点注释

**Files:**
- Modify: `backend/app/api/stock.py`
- Modify: `backend/app/api/valuation.py`
- Modify: `backend/app/api/watchlist.py`

- [ ] **Step 1: 为 stock.py 补齐注释**

在文件顶部添加:
```python
"""股票数据API，提供股票搜索、基本信息查询和估值历史。"""
```

为每个端点添加 docstring:

```python
@router.get("/search", response_model=List[StockSearchResponse])
def search_stocks(keyword: str = Query(..., description="搜索关键词")):
    """搜索股票（当前为占位实现）。"""
```

```python
@router.get("/{code}", response_model=StockInfo)
def get_stock_info(code: str, db: Session = Depends(get_db)):
    """获取股票基本信息（名称、PE、PB、当前价格）。"""
```

```python
@router.get("/{code}/valuation", response_model=ValuationResult)
def get_valuation(code: str, model_code: str = Query("tech", description="估值模型代码"), db: Session = Depends(get_db)):
    """计算并返回股票估值报告（兼容旧接口，推荐使用 /api/valuation/report/{code}）。"""
```

```python
@router.get("/{code}/history", response_model=List[ValuationHistoryItem])
def get_valuation_history(code: str, start_date: date = Query(None), end_date: date = Query(None), db: Session = Depends(get_db)):
    """获取股票估值评分历史（兼容旧接口，推荐使用 /api/valuation/history/{code}）。"""
```

- [ ] **Step 2: 为 valuation.py 补齐注释**

在文件顶部添加:
```python
"""估值API，提供估值报告和估值历史查询。

为什么独立路由模块：估值是系统核心功能，独立路由使URL语义更清晰
（/api/valuation/report/{code} 比 /api/stock/{code}/valuation 更直观）。
"""
```

```python
@router.get("/report/{code}", response_model=ValuationResult)
def get_valuation_report(code: str, model_code: str = Query("tech", description="估值模型代码"), db: Session = Depends(get_db)):
    """获取股票估值报告，包含综合评分、百分位、因子得分详情。"""
```

```python
@router.get("/history/{code}", response_model=List[ValuationHistoryItem])
def get_valuation_history(code: str, start_date: date = Query(None), end_date: date = Query(None), db: Session = Depends(get_db)):
    """获取股票估值评分历史，用于绘制估值趋势曲线。"""
```

- [ ] **Step 3: 为 watchlist.py (API) 补齐注释**

在文件顶部添加:
```python
"""自选股API，提供自选股管理和批量估值计算。"""
```

为 `_batch_calculate` 函数添加:
```python
def _batch_calculate(db: Session) -> dict:
    """批量计算自选股估值的内联实现（WatchlistService 不可用时的降级方案）。"""
```

为各端点添加 docstring:
```python
@router.get("", response_model=List[WatchlistResponse])
def get_watchlist(db: Session = Depends(get_db)):
    """获取自选股列表。"""
```

```python
@router.post("", response_model=WatchlistResponse)
def add_to_watchlist(item: WatchlistItem, db: Session = Depends(get_db)):
    """添加股票到自选列表。"""
```

```python
@router.delete("/{code}")
def remove_from_watchlist(code: str, db: Session = Depends(get_db)):
    """从自选列表删除股票。"""
```

```python
@router.post("/batch")
def batch_calculate(db: Session = Depends(get_db)):
    """批量计算所有自选股的估值评分。"""
```

- [ ] **Step 4: 提交**

```bash
git add backend/app/api/stock.py backend/app/api/valuation.py backend/app/api/watchlist.py
git commit -m "docs: add endpoint docstrings to API layer"
```

---

### Task 8: 为核心配置和数据模型补齐注释

**Files:**
- Modify: `backend/app/core/cache.py`
- Modify: `backend/app/core/config.py`
- Modify: `backend/app/db/models.py`

- [ ] **Step 1: 为 cache.py 补齐注释**

在文件顶部添加:
```python
"""缓存管理模块，提供 Redis 缓存和内存缓存降级。

为什么保留 Redis：Celery Beat/Worker 需要 Redis 作为消息队列，
计算结果缓存也复用同一 Redis 实例。

缓存策略：仅缓存计算量大的衍生数据（MA、波动率），
实时行情和DB数据不缓存（保证数据一致性）。
"""
```

为各函数添加 docstring:
```python
def get_cache():
    """获取 Redis 客户端实例。"""
    return redis_client


def cache_get(key: str):
    """读取缓存值。Redis 不可用时降级到内存缓存。"""
```

```python
def cache_set(key: str, value, expire_seconds: int = 3600):
    """写入缓存值，默认1小时过期。"""
```

```python
def cache_delete(key: str):
    """删除单个缓存键。"""
```

- [ ] **Step 2: 为 config.py 补齐注释**

在文件顶部添加:
```python
"""应用配置模块，通过环境变量和 .env 文件加载配置。

关键配置项：
- DATABASE_URL: SQLite 数据库路径
- REDIS_URL: Redis 连接地址（缓存和 Celery 消息队列共用）
- SECRET_KEY: JWT 签名密钥（生产环境必须修改）
"""
```

- [ ] **Step 3: 为 models.py 补齐表级注释**

```python
class KlineData(Base):
    """K线数据表，存储前复权日K线数据。增量更新，不修改历史记录。"""
    __tablename__ = "kline_data"
```

```python
class ValuationHistory(Base):
    """估值历史表，每日估值评分记录。用于趋势分析和百分位计算。"""
    __tablename__ = "valuation_history"
```

```python
class FinancialData(Base):
    """财务数据表，存储季报/年报数据。更新频率用户可配置。"""
    __tablename__ = "financial_data"
```

```python
class Watchlist(Base):
    """自选股表，记录用户关注的股票及其估值模型配置。"""
    __tablename__ = "watchlist"
```

```python
class SchedulerConfig(Base):
    """定时任务配置表，用户可在设置页面调整频率。"""
    __tablename__ = "scheduler_config"
```

```python
class ModelConfig(Base):
    """估值模型配置表，存储因子组合和权重。支持插件化模型管理。"""
    __tablename__ = "model_config"
```

```python
class User(Base):
    """用户表，单用户密码认证。"""
    __tablename__ = "users"
```

- [ ] **Step 4: 提交**

```bash
git add backend/app/core/cache.py backend/app/core/config.py backend/app/db/models.py
git commit -m "docs: add docstrings to core config, cache, and db models"
```

---

### Task 9: 为前端核心文件补齐 JSDoc 注释

**Files:**
- Modify: `frontend/src/api/index.js`
- Modify: `frontend/src/views/ValuationReport.vue`
- Modify: `frontend/src/views/Home.vue`

- [ ] **Step 1: 为 api/index.js 补齐注释**

在文件顶部添加:
```javascript
/**
 * API 请求模块。
 *
 * 使用 axios 实例统一管理请求，自动附加 JWT token 和 401 跳转登录。
 * baseURL 为 /api，开发环境通过 Vite proxy 转发到后端 8001 端口。
 */
```

为每个 API 对象添加注释:
```javascript
/** 认证 API */
export const authAPI = {
```

```javascript
/**
 * 股票数据 API。
 * 获取股票基本信息和搜索，估值相关调用见 valuationAPI。
 */
export const stockAPI = {
```

```javascript
/**
 * 估值 API。
 * 为什么独立模块：估值是核心功能，独立 API 模块使调用方更清晰。
 */
export const valuationAPI = {
```

```javascript
/** 自选股管理 API */
export const watchlistAPI = {
```

```javascript
/** 定时任务管理 API */
export const schedulerAPI = {
```

```javascript
/** 估值模型和因子管理 API */
export const modelsAPI = {
```

- [ ] **Step 2: 为 ValuationReport.vue 补齐注释**

在 `<script setup>` 标签之后添加:
```javascript
/**
 * 估值报告页面。
 *
 * 为什么单独路由：估值报告是核心功能页面，独立路由便于书签和分享。
 * 数据加载顺序：先获取股票基本信息，再获取估值结果，最后加载历史曲线。
 */
```

- [ ] **Step 3: 为 Home.vue 补齐注释**

在 `<script setup>` 标签之后添加:
```javascript
/**
 * 首页/自选股管理页面。
 *
 * 功能：搜索股票跳转报告、自选股增删、批量估值计算。
 * 搜索是直接跳转到报告页（/valuation/report/:code），无需中间搜索结果页。
 */
```

- [ ] **Step 4: 构建前端验证无语法错误**

Run: `cd /Users/zhanghe/MyProjs/trade/eval_sys/stockTrade/frontend && npm run build`
Expected: 构建成功，无错误

- [ ] **Step 5: 提交**

```bash
git add frontend/src/api/index.js frontend/src/views/ValuationReport.vue frontend/src/views/Home.vue
git commit -m "docs: add JSDoc comments to frontend core files"
```

---

### Task 10: 清空 Redis 旧缓存并最终验证

- [ ] **Step 1: 清空 Redis 中旧格式的缓存数据**

Run: `docker-compose exec -T redis redis-cli FLUSHALL`
Expected: `OK`

- [ ] **Step 2: 重启所有后端服务**

Run: `docker-compose restart backend celery-worker celery-beat`
Expected: 所有服务正常启动

- [ ] **Step 3: 验证核心 API 正常**

Run: `docker-compose exec -T backend python3 -c "
import requests
# 测试股票信息
r1 = requests.get('http://localhost:8000/api/stock/600519')
print('Stock info:', r1.status_code)
# 测试估值报告
r2 = requests.get('http://localhost:8000/api/valuation/report/600519')
print('Valuation report:', r2.status_code)
# 测试估值历史
r3 = requests.get('http://localhost:8000/api/valuation/history/600519')
print('Valuation history:', r3.status_code)
# 测试自选股列表
r4 = requests.get('http://localhost:8000/api/watchlist')
print('Watchlist:', r4.status_code)
"`
Expected: 全部 200

- [ ] **Step 4: 验证 hot reload 生效**

修改 `backend/app/main.py` 的 root 函数返回值，保存，观察 backend 日志:
Run: `docker-compose logs --tail=5 backend`
Expected: 看到 `Reloading...` 和 `Application startup complete`

- [ ] **Step 5: 恢复 main.py 并提交**

```bash
git checkout backend/app/main.py
git commit --allow-empty -m "chore: verify docker dev mode, cache refactor, and comment conventions"
```

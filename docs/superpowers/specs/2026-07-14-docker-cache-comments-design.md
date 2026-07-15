# Docker挂载、缓存策略与注释规范设计

> 日期: 2026-07-14
> 状态: 已批准

## 1. 背景与问题

当前系统存在三个问题：

1. **Docker开发效率低**：每次改代码都需要 `docker-compose build` + 重启，开发迭代慢
2. **缓存策略不合理**：实时行情缓存1小时导致估值基于过期价格；DB数据重复缓存无意义；计算量大的衍生数据反而没缓存
3. **代码缺乏注释**：后端几乎无注释，前端完全没有注释，核心业务逻辑的决策原因不可追溯

## 2. Docker开发模式

### 2.1 方案选择

采用 `docker-compose.override.yml` 方案（Docker Compose官方推荐的开发/生产分离方式）。

- `docker-compose up` → 自动合并 override，开发模式（源码挂载 + hot reload）
- `docker-compose -f docker-compose.yml up` → 跳过 override，生产模式（构建镜像）

### 2.2 实现细节

新建 `docker-compose.override.yml`：

```yaml
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
    command: celery -A app.services.scheduler.celery_app worker --loglevel=info

  celery-beat:
    volumes:
      - ./backend/app:/app/app
    command: celery -A app.services.scheduler.celery_app beat --loglevel=info
```

### 2.3 设计决策

- **只挂载 `app/` 目录**：源码目录，不挂载数据目录（已在主文件挂载）
- **前端不挂载源码**：Vue需要构建步骤，开发时直接在宿主机 `npm run dev`，享受Vite热更新
- **celery-worker 不用 --autoreload**：Celery的autoreload不稳定，改代码后手动重启worker即可
- **保留 `entrypoint.sh` 挂载**：方便修改启动脚本无需重新构建

### 2.4 前端开发流程

开发时不需要Docker：
```bash
cd frontend && npm run dev
```
Vite配置代理到 `localhost:8001`（后端Docker端口）。

生产时仍用Docker nginx部署：
```bash
docker-compose -f docker-compose.yml up -d frontend
```

## 3. 缓存策略重构

### 3.1 核心原则

- 实时数据不缓存（保证最新）
- DB数据不缓存（SQLAlchemy已有连接池+ORM优化）
- 历史估值结果写DB（已有 ValuationHistory 表）
- 仅缓存计算量大的衍生数据（MA、波动率等）

### 3.2 缓存分类矩阵

| 数据类型 | 当前策略 | 改后策略 | 理由 |
|----------|----------|----------|------|
| 实时行情（腾讯API） | 缓存1h | 不缓存 | 价格实时变动，缓存导致估值基于过期价格 |
| K线历史（DB查询） | 缓存1h | 不缓存 | SQLAlchemy连接池已优化，数据不变无需缓存 |
| 财务数据（DB查询） | 缓存7d | 不缓存 | 同上，且更新频率用户可配置 |
| MA/波动率计算 | 不缓存 | 缓存1h | 从K线数据计算MA20/60和波动率，计算量大但结果在数据不变时恒定 |
| 估值百分位 | 不缓存 | 不缓存 | 需实时查DB历史，结果随新数据变化 |
| 估值结果 | 不缓存 | 写DB | 已有ValuationHistory表，每次计算后写入 |
| 自选股列表 | 不缓存 | 不缓存 | 直接DB查询，已有索引，单用户QPS极低 |

### 3.3 实现变更

**移除的缓存**：
- `data_service.get_kline_data()` — 移除Redis缓存，每次直接请求API + DB
- `data_service.get_financial_data()` — 移除Redis缓存，每次直接查DB

**新增的缓存**：
- `data_service.calculate_ma()` — 缓存计算结果
  - key: `calc:ma:{stock_code}:{period}:{latest_date}`
  - TTL: 1小时
  - 失效条件: K线数据更新时清除对应股票的calc缓存
- `data_service.calculate_volatility()` — 同上
  - key: `calc:volatility:{stock_code}:{latest_date}`

**缓存失效**：
- 定时任务更新K线数据后，清除对应股票的 `calc:*` 缓存
- TTL 1小时作为兜底

### 3.4 cache.py 保留

Redis仍需要保留，因为：
- Celery Beat/Worker 需要Redis作为消息队列
- 计算结果缓存仍使用Redis
- `cache.py` 的接口不变，只是调用方减少

## 4. 注释规范

### 4.1 核心原则

- ADR式注释：重点写 why 和简洁的 how
- 不解释显而易见的代码
- 后端用 Google-style docstring
- 前端用 JSDoc 注释块

### 4.2 注释范围

| 层级 | 文件 | 注释要求 |
|------|------|----------|
| API层 | `api/stock.py`, `api/valuation.py`, `api/watchlist.py` | 每个端点写docstring，说明业务意图和关键决策 |
| Service层 | `services/data_service.py`, `services/valuation.py`, `services/watchlist.py` | 类和方法写docstring，解释设计原因 |
| 核心配置 | `core/cache.py`, `core/config.py` | 模块级docstring说明设计决策 |
| 数据模型 | `db/models.py` | 表级注释说明数据关系 |
| 前端 | `api/index.js`, `views/ValuationReport.vue`, `views/Home.vue` | 模块级注释说明功能意图，关键逻辑注释 |
| 不需要 | schemas, `__init__.py`, 简单CRUD | 跳过 |

### 4.3 后端 Google-style 示例

```python
def get_kline_data(self, stock_code: str, ...) -> List[Dict]:
    """获取股票K线数据，合并实时行情和历史数据。

    为什么不缓存实时行情：股票价格实时变动，缓存会导致估值基于过期价格。
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
```

### 4.4 前端 JSDoc 示例

```javascript
/**
 * 估值报告页面。
 *
 * 为什么单独路由：估值报告是核心功能页面，独立路由便于书签和分享。
 * 数据加载顺序：先获取股票基本信息，再获取估值结果，最后加载历史曲线。
 */
```

### 4.5 ADR要点（必须在代码中注释的关键决策）

| 决策 | 位置 | Why |
|------|------|-----|
| 实时数据不缓存 | `data_service.get_kline_data` | 价格实时变动，缓存导致估值不准 |
| JSON序列化而非eval | `data_service._json_serializer` | eval不安全且无法处理日期对象 |
| 估值结果写DB | `valuation.py` API层 | 需要历史趋势分析，DB持久化 |
| K线用前复权 | `data_service.get_kline_data` | 保证技术指标计算一致性 |
| MA/波动率缓存 | `data_service.calculate_ma` | 计算量大但结果在数据不变时恒定 |
| override方式分离环境 | `docker-compose.override.yml` | 官方推荐，自动合并，生产/开发分离 |

## 5. 不做的事情

- 不给 schemas、`__init__.py`、简单CRUD 补注释
- 不引入新的缓存层或中间件
- 不修改前端 Docker 生产部署方式
- 不重构现有架构，仅优化缓存和注释

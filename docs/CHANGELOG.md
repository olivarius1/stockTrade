# Changelog

All notable changes to this project will be documented in this file.

## [1.4.0] - 2026-07-15

### ✨ New Features

- **估值报告页因子得分历史对比**
  - 后端 `/api/valuation/history/{code}` 返回完整因子得分数据
  - 前端支持选择历史日期与最新日期的因子得分对比
  - 两种选日期方式：点击曲线数据点、手动输入（兼容多种日期格式）
  - 单列双进度条对比：上方深色（最新）、下方浅色（历史），同色系区分
  - 每个因子分配固定色系，不同因子色系不同，视觉上一眼区分
  - 选中历史日期时图表上高亮标记（markPoint + 竖直辅助线）

- **估值曲线图优化**
  - 未参与计算的因子标识「未参与」（灰色标注，不渲染进度条）
  - 价格曲线改为浅灰面积图，增强与估值分蓝色线的视觉区分
  - 增加估值分百分位语义色虚线：80%（绿）、40%（橙）、20%（红）

### 🔧 Improvements

- **Docker 开发模式热重载**
  - 新增 `docker-compose.override.yml` 挂载源代码 + uvicorn --reload
- **缓存策略重构**
  - 移除 K线/财务数据缓存，确保实时性和数据一致性
  - MA/波动率计算结果缓存，用 `len(prices)` 作为数据版本标识
- **代码注释规范**
  - 后端补齐 Google-style docstrings，重点写 why
  - 前端补齐 JSDoc 注释，重点写 why

### 🐛 Bug Fixes

- 修复估值历史 API 未返回因子得分字段的问题
- 修复前端路由路径与 API 前缀不一致的问题

### 🗑️ Cleanup

- 删除 `估值系统设计/` 旧目录（脚本已迁移到 `backend/scripts/`，HTML 报告不再需要）
- 删除 `backend/app/data/db_manager.py` 重复文件（已由 `kline_manager.py` 替代）
- 清理 `.gitignore` 中已删除目录的规则

---

## [1.3.0] - 2026-07-14

### 🏗️ Architecture Refactoring

- **代码架构重构**
  - 核心数据层迁移到 `backend/app/data/`
    - `kline_manager.py`（原 `db_manager.py`）：K线数据管理
    - `report_generator.py`（原 `build_report.py`）：估值报告生成
    - `extend_backtest.py`：回测扩展功能
  - 工具脚本迁移到 `backend/scripts/`
    - 选股、批量估值、批量回测、数据迁移等脚本统一管理
  - 静态资源迁移到 `backend/assets/`
    - ECharts 库集中管理
  - 报告输出迁移到 `backend/output/`
    - Docker volume 挂载支持持久化

- **Skills 与工程分离**
  - `.trae/skills/stock-valuation-skill/` 只保留包装脚本
  - 包装脚本通过相对路径调用工程代码
  - 工程不依赖 skills，完全独立
  - 实现：skills 复用工程代码，工程不依赖 skills

### ✨ New Features

- **批量自选股导入**：支持将数据库中所有有估值历史的股票批量加入自选股
  - 新增 `backend/scripts/add_all_to_watchlist.py` 脚本
  - 自动识别股票名称、行业、模型类型
  - 去重处理，跳过已存在的自选股

- **每日数据自动更新定时任务**（凌晨3:00）
  - 新增 `update_kline_and_recalculate` Celery任务
  - 自动增量更新自选股K线数据（前复权）
  - 有新数据时自动重新计算估值分数
  - 将最新估值分数保存到 `valuation_history` 表

- **现有每日估值计算任务**（晚上18:00）
  - 保留原有的 `calculate_watchlist` 任务
  - 每日重新计算所有自选股估值分数

### 🔧 Improvements

- **数据库统一管理**
  - 统一使用 `backend/data/valuation.db` 作为主数据库
  - K线数据、估值历史、自选股数据集中存储
  - 支持增量更新，减少API调用

- **Celery定时任务配置优化**
  - 时区设置为 `Asia/Shanghai`
  - 两个定时任务调度：数据更新（03:00）+ 估值重算（18:00）
  - 任务结果存储到Redis

- **Docker Compose部署完善**
  - Redis服务持久化存储（redis_data volume）
  - Celery Worker 和 Beat 独立容器运行
  - 输出目录持久化（output volume）
  - 所有服务健康检查和自动重启

### 📚 Documentation

- 新增本地部署文档 `docs/local-deploy.md`
- 新增项目状态审计 `docs/project-status-audit-2026-07-13.md`

### 🐛 Bug Fixes

- 修复科创板/创业板新股K线数据缺少 `qfqday` 字段的问题，自动回退到 `day` 字段
- 修复数据库路径不一致问题，统一数据存储位置
- 修复Redis不可用时的内存缓存降级机制

### 📦 Dependencies

- Python 3.12
- FastAPI (latest)
- SQLAlchemy
- Celery 5.x + Redis
- Vue 3 + Vite

---

## [1.2.0] - 2026-07-14

### ✨ New Features

- **批量自选股导入**：支持将数据库中所有有估值历史的股票批量加入自选股
  - 新增 `估值系统设计/add_all_to_watchlist.py` 脚本
  - 自动识别股票名称、行业、模型类型
  - 去重处理，跳过已存在的自选股

- **每日数据自动更新定时任务**（凌晨3:00）
  - 新增 `update_kline_and_recalculate` Celery任务
  - 自动增量更新自选股K线数据（前复权）
  - 有新数据时自动重新计算估值分数
  - 将最新估值分数保存到 `valuation_history` 表

- **现有每日估值计算任务**（晚上18:00）
  - 保留原有的 `calculate_watchlist` 任务
  - 每日重新计算所有自选股估值分数

### 🔧 Improvements

- **数据库统一管理**
  - 统一使用 `backend/data/valuation.db` 作为主数据库
  - K线数据、估值历史、自选股数据集中存储
  - 支持增量更新，减少API调用

- **Celery定时任务配置优化**
  - 时区设置为 `Asia/Shanghai`
  - 两个定时任务调度：数据更新（03:00）+ 估值重算（18:00）
  - 任务结果存储到Redis

- **Docker Compose部署完善**
  - Redis服务持久化存储（redis_data volume）
  - Celery Worker 和 Beat 独立容器运行
  - 所有服务健康检查和自动重启

### 📚 Documentation

- 新增本地部署文档 `docs/local-deploy.md`
- 新增项目状态审计 `docs/project-status-audit-2026-07-13.md`

### 🐛 Bug Fixes

- 修复科创板/创业板新股K线数据缺少 `qfqday` 字段的问题，自动回退到 `day` 字段
- 修复数据库路径不一致问题，统一数据存储位置
- 修复Redis不可用时的内存缓存降级机制

### 📦 Dependencies

- Python 3.12
- FastAPI (latest)
- SQLAlchemy
- Celery 5.x + Redis
- Vue 3 + Vite

---

## [1.1.0] - 2026-07-13

### ✨ New Features

- **GitHub Actions CI/CD 流水线**
  - 单元测试自动运行
  - 前端构建验证
  - Docker镜像构建

- **完整的前端界面**
  - 登录页（简单密码保护）
  - 估值报告页（交互式图表，光标点验）
  - 自选股管理
  - 模型管理器
  - 定时任务配置
  - 系统设置页

- **可插拔估值模型系统**
  - 8种估值模型：必选消费、可选消费、科技制造、周期资源、央企基建、银行保险、地产、医药消费
  - 9+ 估值因子：PE、PB、PEG、MA偏离度、波动率、量能、ROE、股息率、AI分析
  - 因子权重可配置

- **选股模块**
  - 全A股市场基本面筛选
  - 安全边际评分排序
  - 适合估值策略的股票池

### 🔧 Improvements

- 后端API模块化：auth、stock、watchlist、scheduler、models
- Redis缓存支持，降级到内存缓存
- SQLite数据库存储，便于本地部署

---

## [1.0.0] - 2026-07-10

### ✨ Initial Release

- A股估值系统核心框架
- 基于腾讯财经API的K线数据获取
- 前复权价格处理
- 基础估值评分算法
- HTML报告生成（ECharts交互式图表）
- 回测功能（估值百分位策略）
- 止损机制支持

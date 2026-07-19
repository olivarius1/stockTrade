# 本地 Docker Compose 部署记录

## 部署时间

- 2026-07-13

## 当前部署结论

- 已完成开发/生产环境分离部署
- 开发模式：`docker compose up -d`（PG + Redis）+ WSL 本地 Python 后端 + Vite 前端
- 生产模式：`docker compose --profile prod up -d --build`（6 个服务）
- 数据库隔离：生产 `valuation` / 开发 `valuation_dev`
- 生产前端可访问：`http://127.0.0.1:8080`
- 生产后端可访问：`http://127.0.0.1:8001`
- 开发后端可访问：`http://localhost:8000`
- 开发前端可访问：`http://localhost:5173`

## 本次处理内容

1. 检查了项目现有的 `docker-compose.yml`、前后端 `Dockerfile`、后端启动脚本和 `nginx.conf`
2. 验证了 Docker/Compose 环境可用，`docker compose config` 校验通过
3. 解决了默认镜像源无法从 Docker Hub 拉取的问题：
   - `backend/Dockerfile` 改为使用 `docker.m.daocloud.io/library/python:3.12-slim`
   - `frontend/Dockerfile` 改为使用 `docker.m.daocloud.io/library/node:20-alpine`
   - `frontend/Dockerfile` 改为使用 `docker.m.daocloud.io/library/nginx:alpine`
   - `docker-compose.yml` 中的 Redis 镜像改为 `docker.m.daocloud.io/library/redis:7.0-alpine`
4. 解决了宿主机端口冲突问题：
   - 发现本机已有其他 `uvicorn` 进程占用 `8000`
   - 将后端端口映射从 `8000:8000` 调整为 `8001:8000`
5. 修正了前端 `Dockerfile` 的 `FROM ... AS ...` 大小写警告

## 当前端口映射

### 基础设施（开发/生产共用）

| 服务 | 容器端口 | 宿主机端口 | 说明 |
| --- | --- | --- | --- |
| postgres | 5432 | 5432 | PostgreSQL 16 |
| redis | 6379 | 6379 | Redis 7.0 |

### 生产环境应用服务（`--profile prod`）

| 服务 | 容器端口 | 宿主机端口 | 说明 |
| --- | --- | --- | --- |
| frontend | 80 | 8080 | Web 页面入口 |
| backend | 8000 | 8001 | FastAPI API |

### 开发环境

| 服务 | 端口 | 说明 |
| --- | --- | --- |
| backend（WSL 本地） | 8000 | uvicorn 直接运行 |
| frontend（Vite dev） | 5173 | npm run dev，代理 /api 到 8000 |

## 验证结果

### 容器状态

`docker compose ps -a` 验证通过，以下服务均为 `Up`：

- `stocktrade-backend-1`
- `stocktrade-frontend-1`
- `stocktrade-redis-1`
- `stocktrade-celery-worker-1`
- `stocktrade-celery-beat-1`

### HTTP 验证

- `GET http://127.0.0.1:8001/` 返回 `200`
- `GET http://127.0.0.1:8001/openapi.json` 返回 `200`
- `GET http://127.0.0.1:8080` 返回 `200`

### 后端日志

后端日志显示：

- 数据库初始化完成
- Uvicorn 正常启动
- 服务监听于容器内 `0.0.0.0:8000`

### Celery/Redis 状态

- `celery-worker` 已连接 Redis 并进入 `ready`
- `celery-beat` 已正常启动
- `redis` 已就绪并接受连接

## 启动与停止命令

### 开发模式（WSL 本地 Python + Vite）

```bash
# 1. 启动基础设施（PostgreSQL + Redis）
docker compose up -d

# 2. WSL 中初始化开发数据库表结构
cd backend
python init_db.py

# 3. 启动本地后端（热重载）
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 4. 启动前端开发服务器（另一个终端）
cd frontend
npm install
npm run dev

# 或使用后端快捷脚本
bash scripts/dev.sh
```

### 生产模式（全 Docker）

```bash
docker compose --profile prod up -d --build
```

### 查看状态

```bash
# 仅基础设施
docker compose ps

# 含生产服务
docker compose --profile prod ps

# 日志
docker compose --profile prod logs --tail=100
```

### 停止

```bash
# 停止生产应用（保留基础设施供开发使用）
docker compose --profile prod stop backend frontend celery-worker celery-beat

# 停止全部
docker compose --profile prod down
```

## 访问说明

### 开发环境

- 前端页面：`http://localhost:5173`（Vite dev server，/api 代理到后端 8000）
- 后端接口：`http://localhost:8000`
- 后端 OpenAPI：`http://localhost:8000/docs`

### 生产环境

- 前端首页：`http://127.0.0.1:8080`
- 后端接口：`http://127.0.0.1:8001`
- 前端容器内通过 `/api/` 反向代理到 `backend:8000`

## 已知情况

- Redis 启动时有 `vm.overcommit_memory` 警告，但不影响当前本地开发部署
- Celery 以 root 用户运行，当前能正常工作，但生产环境建议切换为非 root 用户

## 备注

- 后端启动脚本会执行 `python init_db.py`
- 初始化逻辑会在数据库中创建默认管理员用户：`admin / admin123`

---

## 2026-07-19 更新：WSL 环境重新部署

### 环境说明

- 操作系统：WSL 2 (Ubuntu 24.04)
- Docker：通过 Docker Desktop WSL Integration 提供（v28.1.1）
- Docker Compose：v2.35.1

### WSL 中 Docker 不可用的排查

在 WSL 中执行 `docker` 命令提示 `not found` 时，**无需在 WSL 内单独安装 Docker Engine**。

原因与解决：
- 大概率是 Windows 宿主机的 **Docker Desktop 未启动** 或未启用 WSL 集成
- 解决方法：打开 Docker Desktop → Settings → Resources → WSL Integration → 启用对应发行版

### 开发环境 vs 生产环境

项目使用 Docker Compose **profiles** 机制分离环境：

| 模式 | 启动命令 | 运行服务 |
|------|----------|----------|
| 开发 | `docker compose up -d` | postgres + redis（基础设施） |
| 生产 | `docker compose --profile prod up -d --build` | 全部 6 个服务 |

**数据库隔离（共用 PG/Redis 实例，逻辑分离）：**

| 环境 | PostgreSQL 库 | Redis db |
|------|---------------|----------|
| 生产 | `valuation` | 0 / 1 |
| 开发 | `valuation_dev` | 2 / 3 |

**开发环境配置：**
- 后端在 WSL 本地 Python 运行（端口 8000，支持 `--reload` 热重载）
- 环境变量文件：`backend/.env`（pydantic-settings 自动读取）
- 快捷启动脚本：`backend/scripts/dev.sh`

**生产环境部署：**
```bash
docker compose --profile prod up -d --build
```

### 本次部署操作

```bash
# 生产环境启动
docker compose --profile prod up -d --build
```

### 验证结果

所有 6 个服务均为 `Up` 状态：

| 服务 | 状态 | 端口 |
|------|------|------|
| postgres | Up (healthy) | 0.0.0.0:5432->5432 |
| redis | Up | 0.0.0.0:6379->6379 |
| frontend | Up | 0.0.0.0:8080->80 |
| backend | Up | 0.0.0.0:8001->8000 |
| celery-worker | Up | - |
| celery-beat | Up | - |

- `GET http://localhost:8080/` → 200
- `GET http://localhost:8001/api/stock/list` → 正常响应

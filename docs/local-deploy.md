# 本地 Docker Compose 部署记录

## 部署时间

- 2026-07-13

## 当前部署结论

- 已完成 `docker compose` 本地部署
- 5 个服务均已启动：`backend`、`frontend`、`redis`、`celery-worker`、`celery-beat`
- 前端可访问：`http://127.0.0.1:8080`
- 后端可访问：`http://127.0.0.1:8001`
- 后端 OpenAPI：`http://127.0.0.1:8001/openapi.json`

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

| 服务 | 容器端口 | 宿主机端口 | 说明 |
| --- | --- | --- | --- |
| frontend | 80 | 8080 | Web 页面入口 |
| backend | 8000 | 8001 | FastAPI API |
| redis | 6379 | 未暴露 | 仅供容器内访问 |

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

### 启动

```bash
docker compose up -d --build
```

### 查看状态

```bash
docker compose ps -a
docker compose logs --tail=100
```

### 停止

```bash
docker compose down
```

## 访问说明

- 前端首页：`http://127.0.0.1:8080`
- 后端接口：`http://127.0.0.1:8001`
- 前端容器内通过 `/api/` 反向代理到 `backend:8000`

## 已知情况

- 宿主机 `8000` 当前被其他项目的 `uvicorn` 进程占用，因此本项目后端改为对外暴露 `8001`
- Redis 启动时有 `vm.overcommit_memory` 警告，但不影响当前本地开发部署
- Celery 以 root 用户运行，当前能正常工作，但生产环境建议切换为非 root 用户

## 备注

- 后端启动脚本会执行 `python init_db.py`
- 初始化逻辑会在数据库中创建默认管理员用户：`admin / admin123`

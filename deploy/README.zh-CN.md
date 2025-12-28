# 部署 ZenetHunter（本地和 UGREEN NAS）

本指南展示如何在开发工作站和 **UGREEN NASync DXP4800 Plus (UGOS Pro)** 上使用 Docker Compose 构建和运行 ZenetHunter。

> TL;DR：使用 `/deploy` 下提供的多阶段 Dockerfile 和 `docker-compose.yml`。通过环境变量配置运行时（参见 `env/.env.example`）。

---

## 1) 先决条件

- 在您的机器上安装 **Docker & Compose**（或通过其 Docker 应用/Portainer 在 UGREEN NAS 上可用）。在 UGREEN 上，UGOS Pro 提供 Docker 应用，您也可以安装 **Portainer** 作为可选的管理 UI。
- **硬件**上下文（DXP4800 Plus）：Intel® Pentium® Gold 8505 (5C/6T)，8GB DDR5（可扩展至 64GB），UGOS Pro。这会影响工作进程数量和资源限制。

---

## 2) 本地构建和运行（开发机器）

从仓库根目录：

```bash
# 1) 准备环境
cd deploy
cp -n env/.env.example env/.env   # 根据需要编辑值

# 2) 构建镜像（多阶段：后端和前端）
docker compose build

# 3) 启动服务（db → backend → frontend）
docker compose up -d

# 4) 检查健康状态
docker compose ps
# 或 curl http://localhost:8000/healthz

# 5) 停止
# docker compose down
```

CI 说明：GitHub Actions "image-check" 工作流执行仅构建验证（拉取最新基础镜像，不推送）；本地优先使用 `docker compose build` 进行验证。

- 默认容器端口：**8000/tcp**（后端 API），**8080/tcp**（通过 nginx 的前端）。主机映射（compose 默认）：**1226 → 8080** 用于前端。健康检查内置到两个镜像中（后端 `/healthz`，前端根 `/`）。

---

## 3) UGREEN NAS (UGOS Pro) 部署

在 UGREEN NAS 上运行容器有两种常见方式：

### 选项 A — 通过 NAS Docker/Compose (CLI)

1. 在 NAS 上**启用 SSH**（UGOS 设置）并以管理员用户 SSH 登录。
2. 确保 **Docker 应用**在 UGOS 上可用/激活。（UGREEN 的应用中心暴露系统应用，包括 Docker。）
3. 将项目复制到 NAS（例如，到共享文件夹）或在 NAS 上**git clone**。
4. 在项目的 `deploy/` 目录内，创建运行时环境：
   ```bash
   cp -n env/.env.example env/.env
   vi env/.env  # 设置 VITE_API_BASE、CORS_ORIGINS 等
   ```
5. 构建并启动：
   ```bash
   docker compose build
   docker compose up -d
   ```
6. 访问：
  - 前端：`http://<NAS-IP>:1226/`  （映射到容器 8080）
  - API：`http://<NAS-IP>:8000/` （健康：`/healthz`）

> 提示：将**卷放在 SSD**（例如 M.2）上用于容器可写数据，以避免保持 HDD 旋转并提高响应性。社区用户建议将 Docker 应用数据放在 SSD 上用于 UGOS。

### 选项 B — 通过 Portainer (UI)

1. 在 NAS 上安装 Portainer（从 UGOS 的应用中心（如果可用）或运行官方容器）。社区指南显示 Portainer 在 UGREEN 上运行良好。
2. 在 Portainer 中，**添加堆栈**并粘贴 `deploy/docker-compose.yml` 的内容。根据数据集路径调整环境变量和卷。
3. 部署堆栈。使用 Portainer 的**健康**和**日志**视图验证服务就绪状态。

> 注意：一些用户报告在 UGOS 中映射 `/var/run/docker.sock` 时感到困惑。如果使用 Portainer 的**本地**套接字，确保 Docker 守护程序正在运行且套接字可访问；否则使用"**Agent**"部署模型。

---

## 4) 端口、卷和重启策略（概述）

| 服务   | 容器端口 | 主机端口（默认） | 卷（默认）                     | 重启策略        |
|-----------|-----------------|---------------------|---------------------------------------|-----------------------|
| backend   | 8000            | 8000                | （不需要绑定）              | `unless-stopped`      |
| frontend  | 8080            | 1226                | `dist/` 烘焙到镜像              | `unless-stopped`      |
| db        | 5432            | *未发布*     | `db_data:/var/lib/postgresql/data`    | `unless-stopped`      |

- 编辑 `deploy/docker-compose.yml` 以更改**端口映射**或将卷移动到 SSD 池。健康检查门控服务就绪状态，并配置 `depends_on`。

---

## 5) 通过环境配置 (.env)

所有运行时配置都是环境驱动的（12 要素）。应用程序自动从环境变量加载配置，并可选择从 `.env` 文件加载。

### 快速设置

1. 复制示例文件：
   ```bash
   cd deploy
   cp env/.env.example env/.env
   ```

2. 编辑 `env/.env` 并根据您的环境自定义值

3. 使用 Docker Compose 时，应用程序会自动从 `env/.env` 加载变量

### 环境特定默认值

应用程序根据 `APP_ENV` 应用不同的默认值：

- **开发** (`APP_ENV=development`)：
  - 日志级别：`debug`（如果未明确设置）
  - CORS：允许常见开发端口

- **暂存** (`APP_ENV=staging`)：
  - 日志级别：`info`（如果未明确设置）

- **生产** (`APP_ENV=production`)：
  - 日志级别：`warning`（如果未明确设置）
  - CORS：**必须明确配置**（如果未设置则警告）

### 关键配置变量

| 变量 | 示例 | 描述 |
|---|---|---|
| `APP_ENV` | `production` | 环境：`development`/`staging`/`production` |
| `CORS_ALLOW_ORIGINS` | `http://<NAS-IP>:8080` | 逗号分隔的 CORS 源（对于 NAS，包括 nginx 主机） |
| `DATABASE_URL` | `postgresql://zenethunter:zenethunter@db:5432/zenethunter` | PostgreSQL DSN（Compose 使用服务名 `db`） |
| `LOG_LEVEL` | `info` | 日志级别：`debug`/`info`/`warning`/`error`/`critical` |
| `API_TITLE` | `ZenetHunter API` | API 标题（OpenAPI 文档） |
| `API_VERSION` | `0.1.0` | API 版本（OpenAPI 文档） |

**注意**：直接在 `docker-compose.yml` 中设置的环境变量优先于 `.env` 文件值。

另请参见：`backend/app/core/config.py` 和 `backend/README.md`。

---

## 6) DXP4800 Plus 上的扩展、资源和 CPU

- DXP4800 Plus 使用 **Intel Pentium Gold 8505**（5 核/6 线程）。使用适中的工作进程数（1–2）启动 Uvicorn，优先使用异步 I/O。除非已调度，否则避免在 NAS 上执行重 CPU 任务。
- 保持扫描间隔保守，并在可能的情况下考虑将嘈杂工作负载固定到 SSD。社区建议建议在 M.2 SSD 上运行 Docker 工作负载以获得快速的用户体验。

---

## 7) 升级和回滚

- 拉取最新代码，然后重建：
  ```bash
  docker compose pull   # 如果稍后使用远程镜像
  docker compose build  # 用于本地构建
  docker compose up -d --no-deps --build backend frontend
  ```
- 回滚：保留之前的镜像标记（例如 `:v0.1.0`），或 `docker image ls` 并使用已知良好的标记 `docker compose up -d`。

---

## 8) 故障排除

- **前端启动，API 404** → 检查 `VITE_API_BASE` 和 **CORS_ORIGINS**；验证后端 `/healthz`。
- **Compose 抱怨 `name:`** → 某些较旧的 Compose 版本不支持顶级 `name`。设置 `COMPOSE_PROJECT_NAME=zenethunter` 或删除 `name:`。
- **Portainer 无法连接到 Docker** → 验证 UGOS 上的 Docker 守护程序/套接字，或部署 Portainer **Agent** 并通过 TCP 连接。
- **性能（缩略图/元数据慢）** → 将容器数据存储在 SSD 上，而不是 HDD 池（社区提示）。

---

## 9) 安全注意事项

- 仅在受信任的 LAN 上暴露端口；如果可用，使用 NAS 防火墙。
- 保持镜像最新；CI 使用仅构建验证来及早发现问题。
- **默认非 root**：后端和前端以非 root 运行；Compose 设置 `user: "101:101"`、`read_only: true` 和 `tmpfs: /tmp`。
- 永远不要提交真实密钥；通过环境或密钥存储注入。

---

## 10) 参考资料和进一步阅读

- UGREEN NASync DXP4800 Plus 产品页面/规格（UGOS Pro、CPU/RAM、托架）。
- UGOS Pro – 应用中心/系统应用概述（包括 Docker）。
- UGREEN NAS 上的 Portainer（社区操作指南）。
- Docker 存储的社区提示（将应用数据放在 SSD 上）。

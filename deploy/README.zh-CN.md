# 部署 ZenetHunter（本地和UGREEN NAS）

本指南说明如何在开发者工作站和**UGREEN NASync DXP4800 Plus (UGOS Pro)** 上使用 Docker Compose **构建和运行** ZenetHunter。

> 简而言之：使用 `/deploy` 目录下提供的多阶段 Dockerfiles 和 `docker-compose.yml`。通过环境变量配置运行时（参见 `env/.env.example`）。

---

## 1) 前提条件

- 在您的机器上安装 **Docker 和 Compose**（或通过 Docker 应用/Portainer 在优越者 NAS 上使用）。在优越者 NAS 上，UGOS Pro 提供 Docker 应用，您还可以安装 **Portainer** 作为可选的管理界面。
- **硬件**环境（DXP4800 Plus）：Intel® Pentium® Gold 8505（5核/6线程），8GB DDR5（可扩展至 64GB），UGOS Pro。这些信息用于确定工作进程数量和资源限制。

---

## 2) 本地构建和运行（开发机器）

从仓库根目录：

```bash
# 1) 准备环境
cd deploy
cp -n env/.env.example env/.env   # 根据需要编辑值

# 2) 构建镜像（多阶段：后端和前端）
docker compose build

# 3) 启动服务（数据库 → 后端 → 前端）
docker compose up -d

# 4) 检查健康状态
docker compose ps
# 或 curl http://localhost:8000/healthz

# 5) 停止
# docker compose down
```

- 默认端口：**8000/tcp**（后端 API），**8080/tcp**（通过 nginx 的前端）。查看 `docker-compose.yml` 中的映射并根据需要编辑。已为每个服务定义了健康检查。（后端 `/healthz`。）

---

## 3) UGREEN NAS（UGOS Pro）部署

在 UGREEN NAS 上运行容器有两种常见方式：

### 方案 A — 通过 NAS Docker/Compose（命令行）

1. 在 NAS 上**启用 SSH**（UGOS 设置）并以管理员用户身份 SSH 登录。
2. 确保 UGOS 上的 **Docker 应用**可用/已激活。（优越者的应用中心提供系统应用，包括 Docker。）
3. 将项目复制到 NAS（例如，复制到共享文件夹）或在 NAS 上 **git clone**。
4. 在项目的 `deploy/` 目录中，创建运行时环境：
   ```bash
   cp -n env/.env.example env/.env
   vi env/.env  # 设置 VITE_API_BASE、CORS_ORIGINS 等
   ```
5. 构建和启动：
   ```bash
   docker compose build
   docker compose up -d
   ```
6. 访问：
  - 前端：`http://<NAS-IP>:8080/`
  - API：`http://<NAS-IP>:8000/`（健康检查：`/healthz`）

> 提示：将**卷保存在 SSD**（如 M.2）上以避免 HDD 持续运转并提高响应速度。社区用户建议将 Docker 应用数据放在 UGOS 的 SSD 上。

### 方案 B — 通过 Portainer（UI）

1. 在 NAS 上安装 Portainer（可以从 UGOS 应用中心安装（如果可用），或通过运行官方容器）。社区指南显示 Portainer 在优越者上运行良好。
2. 在 Portainer 中，**添加堆栈**并粘贴 `deploy/docker-compose.yml` 的内容。调整环境变量和卷以匹配您的数据集路径。
3. 部署堆栈。使用 Portainer 的**健康**和**日志**视图验证服务就绪状态。

> 注意：一些用户报告在 UGOS 中映射 `/var/run/docker.sock` 时感到困惑。如果使用 Portainer 的**本地**套接字，请确保 Docker 守护进程正在运行且套接字可访问；否则使用"**Agent**"部署模式。

---

## 4) 端口、卷和重启策略（概述）

| 服务      | 容器端口        | 主机端口（默认）   | 卷（默认）                           | 重启策略            |
|-----------|-----------------|---------------------|---------------------------------------|--------------------|
| backend   | 8000           | 8000                | （暂不需要绑定）                      | `unless-stopped`   |
| frontend  | 80 (nginx)     | 8080                | `dist/` 已烘焙到镜像中                | `unless-stopped`   |
| db        | 5432           | *未公开*            | `db_data:/var/lib/postgresql/data`    | `unless-stopped`   |

- 编辑 `deploy/docker-compose.yml` 以更改**端口映射**或将卷移动到 SSD 存储池。健康检查控制服务就绪状态，并已配置 `depends_on`。

---

## 5) 通过环境配置（.env）

所有运行时配置都通过环境驱动（12-Factor）。使用 `deploy/env/.env.example` 作为模板：

- **CORS_ORIGINS**：对于 NAS 默认设置，包括 nginx 主机源，例如 `http://<NAS-IP>:8080`。
- **VITE_API_BASE**：前端用它调用 API；在 NAS 上，设置 `VITE_API_BASE=http://<NAS-IP>:8000`。
- **DATABASE_URL**：Compose 通过服务名称连接后端 → `db`。对于外部数据库，替换为该 DSN。
- **LOG_LEVEL**：`debug|info|warning|error|critical`（后端）。

另见：`backend/app/core/config.py`。

---

## 6) DXP4800 Plus 上的扩展、资源和 CPU

- DXP4800 Plus 使用 **Intel Pentium Gold 8505**（5核/6线程）。以适度的工作进程数（1-2）启动 Uvicorn，并优先使用异步 I/O。除非经过调度，否则避免在 NAS 上进行重 CPU 任务。
- 保持扫描器间隔保守，并考虑将噪声工作负载固定到 SSD（如果可能）。社区建议将 Docker 工作负载放在 M.2 SSD 上以获得流畅的用户体验。

---

## 7) 升级和回滚

- 拉取最新代码，然后重建：
  ```bash
  docker compose pull   # 如果以后使用远程镜像
  docker compose build  # 用于本地构建
  docker compose up -d --no-deps --build backend frontend
  ```
- 回滚：保留带标签的以前的镜像（例如，`:v0.1.0`），或 `docker image ls` 并使用已知正常的标签 `docker compose up -d`。

---

## 8) 故障排除

- **前端启动，API 404** → 检查 `VITE_API_BASE` 和 **CORS_ORIGINS**；验证后端 `/healthz`。
- **Compose 抱怨 `name:`** → 一些较老的 Compose 版本不支持顶级 `name`。设置 `COMPOSE_PROJECT_NAME=zenethunter` 或删除 `name:`。
- **Portainer 无法连接到 Docker** → 验证 UGOS 上的 Docker 守护进程/套接字，或部署 Portainer **Agent** 并通过 TCP 连接。
- **性能（缩略图/元数据慢）** → 将容器数据存储在 SSD 上，而不是 HDD 存储池（社区提示）。

---

## 9) 安全说明

- 仅在受信任的局域网上暴露端口；如果可用，使用 NAS 防火墙。
- 保持镜像更新。首选**非 root** 容器（我们的后端镜像已经以非 root 用户运行）。
- 永远不要提交真实的密钥；通过环境或密钥存储注入。

---

## 10) 参考和进一步阅读

- UGREEN NASync DXP4800 Plus 产品页面/规格（UGOS Pro、CPU/RAM、托架）。
- UGOS Pro – 应用中心/系统应用概述（包括 Docker）。
- Portainer NAS 上的 Portainer（社区操作指南）。
- 关于 Docker 存储的社区提示（将应用数据使用 SSD）。


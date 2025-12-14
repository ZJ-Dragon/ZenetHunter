# UGREEN DXP4800 Plus 部署指引

> 本指南专门针对 **UGREEN NASync DXP4800 Plus (UGOS Pro)** 部署 ZenetHunter 的详细说明和最佳实践。

---

## 目录

1. [硬件规格](#1-硬件规格)
2. [系统要求](#2-系统要求)
3. [准备工作](#3-准备工作)
4. [部署方法](#4-部署方法)
5. [存储优化](#5-存储优化)
6. [网络配置](#6-网络配置)
7. [性能调优](#7-性能调优)
8. [故障排除](#8-故障排除)
9. [维护与升级](#9-维护与升级)
10. [参考资源](#10-参考资源)

---

## 1. 硬件规格

### DXP4800 Plus 关键规格

- **CPU**: Intel® Pentium® Gold 8505 (5核心/6线程)
- **内存**: 8GB DDR5 (可扩展至 64GB)
- **存储接口**:
  - 4× SATA 3.5"/2.5" 硬盘位
  - 2× M.2 NVMe SSD 插槽 (2280)
- **网络**: 2× 2.5GbE 网口 (支持链路聚合)
- **操作系统**: UGOS Pro (基于 Linux)

### 性能特点

- **CPU 性能**: 适合轻量级容器工作负载，建议限制 CPU 密集型任务
- **内存**: 8GB 足够运行多个容器，建议为 Docker 预留至少 2GB
- **存储**: M.2 SSD 提供最佳性能，建议将 Docker 数据存储在 SSD 上

---

## 2. 系统要求

### UGOS Pro 要求

- **系统版本**: UGOS Pro (最新稳定版)
- **Docker**: 通过应用中心安装 Docker 应用
- **SSH**: 启用 SSH 访问（用于命令行部署）
- **存储空间**: 至少 10GB 可用空间（推荐 SSD）

### 网络要求

- **局域网访问**: 确保 NAS 与部署设备在同一局域网
- **端口可用性**: 确保端口 8000、1226 未被占用
- **防火墙**: 如启用防火墙，需开放相应端口

---

## 3. 准备工作

### 3.1 启用 SSH

1. 登录 UGOS Pro 管理界面
2. 进入 **系统设置** → **SSH**
3. 启用 SSH 服务
4. 记录 SSH 端口（默认 22）

### 3.2 安装 Docker

1. 打开 **应用中心**
2. 搜索并安装 **Docker** 应用
3. 等待安装完成并启动 Docker 服务
4. 验证安装：
   ```bash
   docker --version
   docker compose version
   ```

### 3.3 准备存储

**重要**: 将 Docker 数据存储在 M.2 SSD 上以获得最佳性能。

1. 在 UGOS Pro 中创建存储池（如果尚未创建）
2. 确保至少有一个 M.2 SSD 可用
3. 在 SSD 上创建共享文件夹（例如：`/mnt/ssd/docker`）
4. 配置 Docker 数据目录指向 SSD（可选，通过 Docker 设置）

> **社区建议**: 将 Docker 应用数据目录配置在 SSD 上，避免 HDD 持续运转，提升响应速度。

---

## 4. 部署方法

### 方法 A: SSH 命令行部署（推荐）

#### 步骤 1: 获取项目代码

```bash
# SSH 登录到 NAS
ssh admin@<NAS-IP>

# 选择存储位置（推荐 SSD 上的共享文件夹）
cd /mnt/ssd/projects  # 或您选择的路径

# 克隆项目
git clone https://github.com/ZJ-Dragon/ZenetHunter.git
cd ZenetHunter
```

#### 步骤 2: 配置环境变量

```bash
cd deploy

# 创建环境变量文件
cp env/.env.example env/.env

# 编辑环境变量
vi env/.env  # 或使用您喜欢的编辑器
```

**关键配置项**:

```bash
# 环境设置
APP_ENV=production

# CORS 配置（使用 NAS IP）
CORS_ALLOW_ORIGINS=http://<NAS-IP>:1226,http://<NAS-IP>:8080

# 数据库配置（使用服务名 'db'）
DATABASE_URL=postgresql://zenethunter:zenethunter@db:5432/zenethunter

# 日志级别
LOG_LEVEL=info
```

#### 步骤 3: 构建和启动

```bash
# 构建镜像（首次部署或更新代码后）
docker compose build

# 启动所有服务
docker compose up -d

# 查看服务状态
docker compose ps

# 查看日志
docker compose logs -f
```

#### 步骤 4: 验证部署

```bash
# 检查健康状态
curl http://localhost:8000/healthz

# 或从局域网其他设备访问
curl http://<NAS-IP>:8000/healthz
```

**访问地址**:
- 前端: `http://<NAS-IP>:1226`
- 后端 API: `http://<NAS-IP>:8000`
- API 文档: `http://<NAS-IP>:8000/docs`

### 方法 B: Portainer UI 部署

#### 步骤 1: 安装 Portainer

1. 在应用中心搜索 **Portainer**
2. 安装并启动 Portainer
3. 访问 Portainer Web UI: `http://<NAS-IP>:9000`
4. 完成初始设置

#### 步骤 2: 创建 Stack

1. 在 Portainer 中，进入 **Stacks** → **Add stack**
2. 命名: `zenethunter`
3. 选择 **Web editor**
4. 将 `deploy/docker-compose.yml` 内容粘贴到编辑器
5. 配置环境变量（在 **Environment variables** 部分）
6. 点击 **Deploy the stack**

#### 步骤 3: 验证部署

1. 在 Portainer 中查看 **Containers** 状态
2. 所有容器应显示为 **Running**
3. 检查 **Logs** 确认无错误

---

## 5. 存储优化

### 5.1 Docker 数据目录配置

**推荐**: 将 Docker 数据目录配置在 SSD 上。

1. 停止 Docker 服务
2. 在 UGOS Pro 设置中，将 Docker 数据目录指向 SSD 路径
3. 重启 Docker 服务

### 5.2 卷映射优化

在 `docker-compose.yml` 中，可以自定义卷映射位置：

```yaml
volumes:
  db_data:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: /mnt/ssd/docker/zenethunter/db_data
```

### 5.3 存储池建议

- **SSD 存储池**: 用于 Docker 数据、数据库、日志
- **HDD 存储池**: 用于大文件、备份、归档数据

---

## 6. 网络配置

### 6.1 端口映射

默认端口配置：

| 服务 | 容器端口 | 主机端口 | 说明 |
|------|----------|----------|------|
| Backend | 8000 | 8000 | API 服务 |
| Frontend | 8080 | 1226 | Web 界面 |
| Database | 5432 | - | 内部网络 |

### 6.2 防火墙配置

如果启用了 UGOS Pro 防火墙：

1. 进入 **系统设置** → **防火墙**
2. 添加规则：
   - 端口 8000 (TCP) - 后端 API
   - 端口 1226 (TCP) - 前端界面
3. 保存并应用

### 6.3 链路聚合（可选）

DXP4800 Plus 支持双 2.5GbE 链路聚合：

1. 进入 **网络设置** → **链路聚合**
2. 配置两个网口为聚合模式
3. 提升网络带宽（适用于多用户访问）

---

## 7. 性能调优

### 7.1 CPU 限制

考虑到 DXP4800 Plus 的 CPU 性能，建议限制容器资源：

```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '2.0'  # 限制最多使用 2 个 CPU 核心
          memory: 2G
        reservations:
          cpus: '0.5'  # 保证至少 0.5 个核心
          memory: 512M
```

### 7.2 工作进程配置

后端 Uvicorn 工作进程数建议：

- **单进程模式**（默认）: 适合轻量级负载
- **多进程模式**: 如需更高并发，可设置 `--workers 2`（最多 2 个）

> **注意**: DXP4800 Plus 为 5 核 6 线程，建议工作进程数不超过 2。

### 7.3 扫描器间隔

网络扫描任务建议使用保守的间隔：

- 设备扫描: 每 5-10 分钟
- 拓扑发现: 每 15-30 分钟
- 避免频繁扫描导致 CPU 负载过高

### 7.4 数据库优化

PostgreSQL 配置建议（在 `docker-compose.yml` 中）：

```yaml
db:
  environment:
    POSTGRES_SHARED_BUFFERS: 256MB
    POSTGRES_EFFECTIVE_CACHE_SIZE: 1GB
    POSTGRES_MAINTENANCE_WORK_MEM: 64MB
```

---

## 8. 故障排除

### 8.1 服务无法启动

**问题**: 容器启动后立即退出

**排查步骤**:
```bash
# 查看容器日志
docker compose logs <service-name>

# 检查容器状态
docker compose ps

# 检查资源使用
docker stats
```

**常见原因**:
- 端口被占用
- 内存不足
- 配置文件错误
- 权限问题

### 8.2 前端无法访问后端 API

**问题**: 前端显示 API 错误

**排查步骤**:
1. 检查后端健康状态: `curl http://<NAS-IP>:8000/healthz`
2. 检查 CORS 配置: 确保 `CORS_ALLOW_ORIGINS` 包含前端 URL
3. 检查网络连接: `docker compose exec backend ping db`

### 8.3 数据库连接失败

**问题**: 后端无法连接数据库

**排查步骤**:
```bash
# 检查数据库容器状态
docker compose ps db

# 查看数据库日志
docker compose logs db

# 测试数据库连接
docker compose exec backend python -c "import psycopg2; psycopg2.connect('postgresql://zenethunter:zenethunter@db:5432/zenethunter')"
```

### 8.4 性能问题

**问题**: 系统响应缓慢

**优化建议**:
1. 将 Docker 数据移至 SSD
2. 减少工作进程数
3. 增加扫描间隔
4. 检查是否有其他高负载应用

### 8.5 存储空间不足

**问题**: 磁盘空间不足

**清理步骤**:
```bash
# 清理未使用的镜像
docker image prune -a

# 清理未使用的卷
docker volume prune

# 清理构建缓存
docker builder prune
```

---

## 9. 维护与升级

### 9.1 日常维护

**定期任务**:
- 检查服务状态: `docker compose ps`
- 查看日志: `docker compose logs --tail=100`
- 清理日志文件（如果启用文件日志）
- 备份数据库（重要数据）

### 9.2 升级流程

```bash
# 1. 备份当前配置和数据
cp -r deploy/env/.env deploy/env/.env.backup
docker compose exec db pg_dump -U zenethunter zenethunter > backup.sql

# 2. 拉取最新代码
git pull origin main

# 3. 重建镜像
docker compose build

# 4. 重启服务（零停机升级）
docker compose up -d --no-deps --build backend frontend

# 5. 验证服务
docker compose ps
curl http://localhost:8000/healthz
```

### 9.3 回滚

如果升级后出现问题：

```bash
# 恢复配置
cp deploy/env/.env.backup deploy/env/.env

# 使用之前的镜像标签（如果已标记）
docker compose pull
docker compose up -d

# 或恢复数据库备份
docker compose exec -T db psql -U zenethunter zenethunter < backup.sql
```

---

## 10. 参考资源

### 官方资源

- **UGREEN 官网**: https://www.ugreen.com
- **DXP4800 Plus 产品页**: https://www.ugreen.com/products/usa-35260a
- **UGOS Pro 文档**: 通过 UGOS Pro 管理界面访问

### 社区资源

- **UGREEN 社区论坛**: 搜索 "DXP4800 Plus" 相关讨论
- **Docker 最佳实践**: https://docs.docker.com/develop/dev-best-practices/
- **Portainer 文档**: https://docs.portainer.io/

### 技术支持

- **UGREEN 技术支持**: 通过官网联系
- **项目 Issues**: https://github.com/ZJ-Dragon/ZenetHunter/issues

---

## 附录

### A. 快速参考命令

```bash
# 启动所有服务
docker compose up -d

# 停止所有服务
docker compose down

# 查看服务状态
docker compose ps

# 查看日志
docker compose logs -f

# 重启服务
docker compose restart

# 进入容器
docker compose exec backend bash
docker compose exec db psql -U zenethunter zenethunter
```

### B. 环境变量完整列表

参考 `deploy/env/.env.example` 获取完整的环境变量列表。

### C. 性能监控

```bash
# 查看资源使用
docker stats

# 查看系统资源
htop  # 如果已安装

# 查看磁盘使用
df -h
docker system df
```

---

**最后更新**: 2024-12-09  
**适用版本**: ZenetHunter v0.1.0+  
**UGOS Pro 版本**: 最新稳定版

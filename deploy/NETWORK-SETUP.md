# Docker 网络配置指南 - 网络扫描功能

## 问题说明

如果遇到 `Failed to start scan: timeout of 10000ms exceeded` 错误，通常是因为 Docker 容器的网络限制导致无法进行网络扫描。

## 解决方案

### 方案 1: 使用 Host 网络模式（推荐用于开发环境）

Host 网络模式让容器直接使用主机的网络栈，可以完全访问网络接口和 ARP 表。

**步骤：**

1. 编辑 `deploy/docker-compose.yml`，找到 `backend` 服务配置
2. 添加 `network_mode: "host"`：
   ```yaml
   backend:
     # ... 其他配置 ...
     network_mode: "host"
     # 注释掉或删除 networks: 部分
     # networks:
     #   zh_net:
     #     aliases:
     #       - api
   ```
3. 如果使用 `docker-compose.yml`（根目录），同样添加上述配置
4. 重启服务：
   ```bash
   ./docker-run.sh restart
   # 或
   docker compose restart backend
   ```

**优点：**
- 完全的网络访问权限
- 可以直接访问主机的 ARP 表
- 无需额外的权限配置

**缺点：**
- 降低了容器隔离性
- 端口映射不再需要（直接使用主机端口）

### 方案 2: Bridge 网络 + 额外权限（推荐用于生产环境）

保持容器隔离，但添加必要的网络权限。

**步骤：**

1. 编辑 `deploy/docker-compose.yml`，找到 `backend` 服务配置
2. 添加网络权限和卷挂载：
   ```yaml
   backend:
     # ... 其他配置 ...
     volumes:
       - backend_data:/app/data
       # 挂载 ARP 表（只读）
       - /proc/net/arp:/proc/net/arp:ro
     cap_add:
       - NET_BIND_SERVICE  # 已有
       - NET_ADMIN          # 新增：网络管理权限
       # - NET_RAW          # 可选：原始套接字（Scapy 需要）
   ```
3. 确保网络不是内部网络：
   ```yaml
   networks:
     zh_net:
       driver: bridge
       internal: false  # 确保不是 true
   ```
4. 重启服务

**优点：**
- 保持容器隔离
- 更安全
- 适合生产环境

**缺点：**
- 某些高级网络操作可能仍有限制

### 方案 3: 使用网络配置脚本

我们提供了一个辅助脚本来帮助配置：

```bash
cd deploy
./docker-network-setup.sh check    # 检查当前配置
./docker-network-setup.sh host     # 获取 host 模式配置说明
./docker-network-setup.sh bridge   # 获取 bridge 模式配置说明
```

## 验证配置

配置完成后，可以通过以下方式验证：

1. **检查容器网络模式：**
   ```bash
   docker inspect zh-backend | grep -A 10 "NetworkMode"
   ```

2. **检查 ARP 表访问：**
   ```bash
   docker exec zh-backend cat /proc/net/arp
   ```

3. **查看日志：**
   ```bash
   ./docker-run.sh logs backend
   # 或
   docker logs zh-backend
   ```

4. **测试扫描功能：**
   - 访问前端：http://localhost:1226
   - 进入设备列表页面
   - 点击 "Start Scan" 按钮
   - 查看日志页面 (`/logs`) 查看详细错误信息

## 其他可能的问题

### 问题：扫描超时但网络配置正确

**可能原因：**
- 前端 API 超时时间太短（已修复为 30 秒）
- 扫描初始化过程太慢

**解决方案：**
- 已增加前端超时时间到 30 秒
- 扫描 API 已优化为立即返回，不等待扫描完成

### 问题：权限不足

**症状：**
- 日志显示 "Permission denied" 或 "Operation not permitted"

**解决方案：**
- 确保添加了 `NET_ADMIN` 或 `NET_RAW` 权限
- 或者使用 host 网络模式
- 或者以 root 用户运行（不推荐，仅用于测试）

## 快速修复命令

如果需要快速切换到 host 网络模式：

```bash
# 备份当前配置
cp deploy/docker-compose.yml deploy/docker-compose.yml.backup

# 使用 sed 添加 host 网络模式（macOS）
sed -i '' '/^  backend:/a\
    network_mode: "host"
' deploy/docker-compose.yml

# 注释掉 networks 部分（手动编辑更安全）
# 然后重启
./docker-run.sh restart
```

## 注意事项

1. **Host 网络模式**：在 macOS 和 Windows 上，Docker Desktop 可能不完全支持 host 网络模式。在这些平台上，建议使用方案 2（Bridge + 权限）。

2. **生产环境**：建议使用方案 2（Bridge + 权限），保持更好的安全隔离。

3. **日志查看**：如果扫描失败，查看 `/logs` 页面可以获取详细的错误信息，包括：
   - 系统环境信息
   - 网络能力检测
   - 详细的错误日志

## 需要帮助？

如果问题仍然存在：

1. 查看日志页面 (`http://localhost:1226/logs`) 获取系统信息和错误详情
2. 检查后端日志：`./docker-run.sh logs backend`
3. 验证网络配置：`./deploy/docker-network-setup.sh check`

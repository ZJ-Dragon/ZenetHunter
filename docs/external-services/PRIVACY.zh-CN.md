# 隐私策略：外部识别 Provider

## 概述
ZenetHunter 支持可选的外部识别 Provider，以提升设备识别准确度。本文说明发送的数据、如何减少暴露，以及如何禁用外部查询。

## 外部查询默认关闭
**默认关闭外部识别查询。** 系统在不开启外部 Provider 时仍可正常工作（依赖本地 OUI、DHCP 指纹、mDNS/SSDP 等）。

## 发送哪些数据？
### MACVendors（厂商查询）
- **发送数据**：仅 OUI（MAC 前 3 个八位字节），如 `00:11:22`
- **完整 MAC**：从不发送（隐私保护）
- **示例**：MAC `00:11:22:33:44:55` → 只发送 `00:11:22`
- **隐私级别**：低（仅 OUI，无法定位具体设备）
- **API**：https://api.macvendors.com（公开，无需注册）

### Fingerbank（设备指纹）
- **发送数据**：组合指纹（DHCP 选项、User-Agent 等）
- **隐私级别**：高（更详细的指纹数据）
- **要求**：API Key（https://fingerbank.org 注册）
- **默认**：关闭（需显式配置）

## 隐私保护特性
### 1. OUI-only 模式（默认开启）
当 `EXTERNAL_LOOKUP_OUI_ONLY=true`（默认）时，仅发送 OUI 前缀，不发送完整 MAC。

### 2. 域名白名单
仅允许以下域名：
- `macvendors.com`, `api.macvendors.com`
- `api.fingerbank.org`

其他域名一律阻断。

### 3. 速率限制
- **MACVendors**：1 次/秒，1000 次/天
- **Fingerbank**：0.5 次/秒，500 次/天

### 4. 缓存
所有查询结果本地缓存 7 天，减少外部请求。缓存目录：`backend/data/cache/`（已 gitignore）。

### 5. 审计日志
记录并脱敏：
- Provider 名称
- 查询类型（vendor/device）
- 成功/失败状态
- 缓存命中情况
- **不含敏感数据**（不记录完整 MAC、不记录 API Key、不记录指纹详情）

## 如何禁用外部查询
### 方法 1：环境变量（推荐）
```bash
export FEATURE_EXTERNAL_LOOKUP=false
```

### 方法 2：UI 设置
1. 打开 Settings
2. 找到 “External Lookup”
3. 关闭开关

### 方法 3：`.env` 配置
```
FEATURE_EXTERNAL_LOOKUP=false
```

## 最小化数据暴露
1. **保持 OUI-only**：`EXTERNAL_LOOKUP_OUI_ONLY=true`（默认）
2. **仅启用 MACVendors**：不需要时关闭 Fingerbank
3. **查看审计日志**：了解实际发送内容
4. **利用缓存**：让缓存积累以减少外部调用

## 安全注意事项
- **API Key 不写日志**
- **完整 MAC 不写日志**（仅 OUI 哈希）
- **域名白名单**：阻止未授权域名
- **熔断**：Provider 故障时防止级联失败
- **超时保护**：请求 5–10 秒超时

## 合规
- **GDPR**：最小化数据（默认 OUI-only），需显式启用
- **隐私设计**：默认关闭、仅限主动开启
- **数据最小化**：只发送必要字段

## 手动设备标注
### 概述
管理员可手动给设备添加名称/厂商：
1. **用户自定义标签**：覆盖自动识别
2. **指纹复用**：可对相似设备自动复用手工标签
3. **本地存储**：仅存于本地 SQLite

### 数据存储
- `devices` 表：单设备覆盖（`name_manual`, `vendor_manual`）
- `manual_overrides` 表：指纹级标签，便于复用

### 隐私保护
**手动标签仅本地存储，不会外发**：
- 数据保存在本地 SQLite (`backend/data/zenethunter.db`)
- 无任何外部同步
- 不涉及云端

### 数据库保护
- `backend/data/*.db`、`backend/data/*-wal`、`backend/data/*-shm` 均被 `.gitignore` 排除，避免：
  - 设备信息被提交
  - 手工命名泄露
  - 网络拓扑暴露

### 审计日志
记录但脱敏：操作者、时间、设备（MAC）、应用的标签（无敏感内容）。

### 清除手动标签
- **单设备**：在设备详情中点击“清除手工标签”
- **全部**：删除数据库文件并重启应用

### 指纹键生成
手工标注时会生成“fingerprint key”，来源于：
- DHCP 选项（Vendor Class Identifier、主机名模式）
- mDNS 服务类型
- SSDP Server 头
- OUI 前缀（兜底）

该键：
- **单向哈希**：不可逆
- **非识别性**：不含 MAC/IP
- **仅本地**：仅存本地数据库

## 问题反馈
参见 [EXTERNAL_SERVICES.zh-CN.md](EXTERNAL_SERVICES.zh-CN.md) 获取 Provider 详情，或查看 [SECURITY.zh-CN.md](../../SECURITY.zh-CN.md) 了解安全策略。

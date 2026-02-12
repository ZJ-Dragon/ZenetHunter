# 外部识别服务

## 概述
ZenetHunter 可接入外部识别服务以提升设备识别准确度。本文描述各 Provider 的能力、限制和配置方法。

## Provider
### 1. MACVendors（厂商查询）
- **用途**：依据 MAC 地址 OUI（前 3 字节）识别设备厂商。
- **API**：https://api.macvendors.com
- **特性**：
  - 无需注册/API Key
  - 免费额度：约 1,000 次/天
  - 建议速率：约 1 QPS
  - 隐私：只发送 OUI（前三个八位字节），不发送完整 MAC
- **限制**：
  - 仅厂商级别（无具体型号）
  - 免费额度有限
  - 不提供设备类别/类型
- **使用**：
  ```python
  # FEATURE_EXTERNAL_LOOKUP=true 时自动启用
  # 仅发送 OUI（如 MAC 00:11:22:33:44:55 → 00:11:22）
  ```
- **配置**：
  - 开启：`FEATURE_EXTERNAL_LOOKUP=true`
  - 不需要 API Key

### 2. Fingerbank（设备指纹）
- **用途**：基于综合指纹识别设备型号、类别和厂商。
- **API**：https://api.fingerbank.org
- **特性**：
  - 详细的设备识别（型号、类别）
  - 使用 DHCP、User-Agent 等指纹信息
  - 比 OUI 查询更高的准确度
- **限制**：
  - 需要 API Key（在 https://fingerbank.org 注册）
  - 隐私风险更高（发送指纹数据）
  - 速率限制：约 0.5 QPS，500 次/天
  - 默认关闭
- **使用**：
  ```bash
  export FINGERBANK_API_KEY=your_key_here
  export FEATURE_EXTERNAL_LOOKUP=true
  ```
- **配置**：
  - 开启：`FEATURE_EXTERNAL_LOOKUP=true` 且设置 `FINGERBANK_API_KEY`
  - 隐私：发送指纹数据，暴露度更高

## 识别优先级
当外部查询启用时，识别顺序为：
1. **本地 OUI 查询**（最快，无网络）
2. **本地 DHCP 指纹匹配**（快，无网络）
3. **外部厂商查询**（MACVendors，启用时）
4. **外部设备指纹**（Fingerbank，启用且有 Key 时）

结果会按权重合并。

## 速率限制与缓存
### 速率
- **MACVendors**：1 QPS，1000/天
- **Fingerbank**：0.5 QPS，500/天

系统会自动执行限流，超限返回速率限制错误（不会崩溃）。

### 缓存
- **TTL**：7 天
- **最大条目**：1000（LRU 淘汰）
- **位置**：`backend/data/cache/recognition_cache.json`（已 gitignore）
- **隐私**：缓存键经过哈希处理（无明文 MAC）

## 默认行为
**外部查询默认关闭。**

启用方式：
1. 环境变量 `FEATURE_EXTERNAL_LOOKUP=true`
2. 或在 UI 设置中开启（仅管理员）

**注意**：环境变量默认 `false`（安全默认）。UI 和软件层面还会添加“软限制”。详见 [PRIVACY.zh-CN.md](PRIVACY.zh-CN.md)。

## API
### 获取 Provider 列表
```http
GET /api/recognition/providers
```
返回可用 Provider、状态与限额。

### 更新外部查询开关
```http
POST /api/recognition/settings/external-lookup
Authorization: Bearer <admin_token>
Content-Type: application/json

{
  "enabled": true
}
```
**仅管理员**，更新运行时设置（不会持久化到环境）。

## 故障排查
### Provider 不工作
1. 检查是否已开启 `FEATURE_EXTERNAL_LOOKUP`
2. 检查域名白名单（需允许 Provider 域名）
3. 检查速率限制（可能被限流）
4. 检查熔断状态（Provider 宕机时可能打开）
5. 查看审计日志

### 速率限制错误
- 等待窗口重置
- 查看缓存（命中缓存不计入额度）
- 降低扫描频率

### Fingerbank 未启用
- 确认设置了 `FINGERBANK_API_KEY`
- 确认 `FEATURE_EXTERNAL_LOOKUP=true`
- 通过 `/api/recognition/providers` 检查 Provider 状态

## 参考
- [PRIVACY.zh-CN.md](PRIVACY.zh-CN.md)：隐私与数据最小化
- [SECURITY.zh-CN.md](../../SECURITY.zh-CN.md)：安全策略与域名白名单
- MACVendors API: https://macvendors.com/api
- Fingerbank API: https://fingerbank.org/api

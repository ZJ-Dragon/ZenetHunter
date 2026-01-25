# Active Probe Device Identification

## 概述

主动探测（Active Probe）是一种设备识别技术，通过模拟正常的服务器连接，直接向设备发送请求，让设备自己"供出"名字和型号等信息。

## 工作原理

系统会向设备发送多种协议的请求，模拟正常的客户端连接：

1. **HTTP/HTTPS 请求**：访问设备的 Web 管理界面
2. **Telnet Banner 抓取**：连接 Telnet 端口读取欢迎信息
3. **SSH Banner 抓取**：连接 SSH 端口读取版本信息
4. **打印机协议**：IPP (Internet Printing Protocol) 和 LPD (Line Printer Daemon)
5. **IoT 协议**：CoAP (Constrained Application Protocol)

## 支持的协议和方法

### 1. HTTP/HTTPS 探测

**端口**：80, 8080, 443, 8443, 8000, 8888

**提取的信息**：
- HTTP Server 头（如 "Apache/2.4", "nginx/1.18"）
- X-Powered-By 头（如 "PHP/7.4"）
- HTML `<title>` 标签（如 "Router Admin - TP-Link TL-WR940N"）
- Meta 标签（`<meta name="device">`, `<meta name="model">`）
- HTML 注释中的设备信息

**示例**：
```
GET http://192.168.31.1/
Server: TP-Link Router
Title: TP-Link Router Admin - TL-WR940N
```

### 2. Telnet Banner 抓取

**端口**：23, 2323

**提取的信息**：
- Telnet 欢迎横幅（通常包含设备名称、型号、固件版本）

**示例**：
```
Welcome to TP-Link Router
Model: TL-WR940N
Firmware: 1.0.0
```

### 3. SSH Banner 抓取

**端口**：22

**提取的信息**：
- SSH 版本字符串（如 "SSH-2.0-OpenSSH_7.9"）
- 设备厂商信息（如 "SSH-2.0-Cisco-1.25"）

**示例**：
```
SSH-2.0-Cisco-1.25  # 识别为 Cisco 设备
SSH-2.0-OpenSSH_7.9  # 识别为 Linux/Unix 设备
```

### 4. 打印机协议

**IPP (端口 631)**：
- 发送 Get-Printer-Attributes 请求
- 获取打印机型号、厂商信息

**LPD (端口 515)**：
- 发送接收作业命令
- 检测打印机服务

### 5. IoT 协议

**CoAP (端口 5683)**：
- 发送 GET 请求到 `/.well-known/core`
- 获取 IoT 设备资源列表

## 识别优先级

主动探测的结果具有**最高优先级**（置信度 75-85%），因为这是设备直接提供的信息：

1. **Active Probe** (75-85% 置信度) - 设备直接响应
2. External Device Fingerprint (70% 置信度) - Fingerbank
3. External Vendor (80% 置信度) - MACVendors
4. Local OUI (80% 置信度) - MAC 地址 OUI
5. DHCP Fingerprint (70% 置信度) - 本地规则

## 配置

### 启用/禁用

通过环境变量控制：
```bash
FEATURE_ACTIVE_PROBE=true   # 默认启用
FEATURE_ACTIVE_PROBE=false  # 禁用主动探测
```

### 超时设置

每个设备的探测超时：2 秒
总体超时：3 秒

## 提取的设备信息示例

### HTTP 响应
```json
{
  "http_server": "TP-Link Router",
  "http_title": "TP-Link Router Admin - TL-WR940N",
  "http_port": 80,
  "http_status": 200
}
```

### Telnet Banner
```json
{
  "telnet_banner": "Welcome to TP-Link Router\nModel: TL-WR940N"
}
```

### SSH Banner
```json
{
  "ssh_banner": "SSH-2.0-Cisco-1.25",
  "ssh_vendor": "Cisco"
}
```

## 识别结果示例

当主动探测成功时，识别引擎会：

1. **提取厂商**：从 HTTP title、SSH banner、Telnet banner 中提取
2. **提取型号**：从 HTTP meta 标签、title、banner 中提取
3. **高置信度**：75-85%（因为是设备直接提供的信息）

**示例识别结果**：
```json
{
  "best_guess_vendor": "TP-Link",
  "best_guess_model": "TL-WR940N",
  "confidence": 85,
  "evidence": {
    "sources": ["active_probe_http"],
    "matched_fields": ["http_title", "http_server"]
  }
}
```

## 安全考虑

1. **只读操作**：所有探测都是只读的（GET 请求、Banner 读取），不会修改设备状态
2. **超时保护**：每个探测都有超时限制，避免长时间等待
3. **并发控制**：探测是并发执行的，但每个设备有独立的超时
4. **错误处理**：所有探测失败都会被捕获，不会影响其他探测

## 性能影响

- **并发执行**：所有探测方法（HTTP, Telnet, SSH, Printer, IoT）并发执行
- **快速失败**：如果某个端口不可达，立即尝试下一个
- **总耗时**：每个设备约 2-3 秒（取决于设备响应速度）

## 常见设备识别

### 路由器
- **HTTP**：通常有 Web 管理界面（端口 80/443）
- **Telnet**：部分路由器开放 Telnet（端口 23）
- **识别**：从 HTTP title 和 Server 头提取厂商/型号

### 打印机
- **IPP**：大多数现代打印机支持（端口 631）
- **LPD**：传统打印机支持（端口 515）
- **识别**：从 IPP 响应中提取打印机型号

### IoT 设备
- **HTTP**：很多 IoT 设备有简单的 Web 界面
- **CoAP**：部分 IoT 设备使用 CoAP 协议
- **识别**：从 HTTP 响应或 CoAP 资源中提取

### 服务器/PC
- **SSH**：Linux/Unix 服务器通常开放 SSH（端口 22）
- **HTTP**：Web 服务器（端口 80/443）
- **识别**：从 SSH banner 和 HTTP Server 头识别

## 故障排除

### 探测失败

如果主动探测没有返回结果，可能的原因：
1. 设备防火墙阻止了连接
2. 设备没有开放相关端口
3. 设备需要认证（HTTP 401/403）
4. 超时设置太短

### 提高识别率

1. **增加超时**：如果设备响应慢，可以增加 `timeout` 参数
2. **检查端口**：确认设备实际开放的端口
3. **查看日志**：检查 `active_probe` 相关的调试日志

## 与现有方法的结合

主动探测与以下方法结合使用：
- **mDNS**：发现设备服务
- **SSDP**：获取 UPnP 设备描述
- **OUI 查询**：MAC 地址厂商识别
- **外部 Provider**：MACVendors, Fingerbank

所有方法的结果会合并，使用加权平均计算最终置信度。

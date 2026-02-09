# 主动探测（Active Probe）设备识别

## 概述
主动探测通过模拟正常客户端连接，让设备“自报家门”（厂商、型号、固件）。所有探测均为只读、带超时保护。

## 工作原理
引擎会并发尝试多种协议：
1) **HTTP/HTTPS**：抓取 Web 管理界面
2) **Telnet**：抓取横幅
3) **SSH**：抓取横幅
4) **打印机协议**：IPP、LPD
5) **IoT**：CoAP `/.well-known/core`

## 支持的探测
### HTTP/HTTPS
- **端口**：80、8080、443、8443、8000、8888
- **提取**：`Server` 头、`X-Powered-By`、HTML `<title>`、`<meta name="device/model">`、HTML 注释中的设备信息。
- **示例**
  ```
  GET http://192.168.31.1/
  Server: TP-Link Router
  Title: TP-Link Router Admin - TL-WR940N
  ```

### Telnet 横幅
- **端口**：23、2323
- **提取**：欢迎横幅（常含厂商/型号/固件）。
- **示例**
  ```
  Welcome to TP-Link Router
  Model: TL-WR940N
  Firmware: 1.0.0
  ```

### SSH 横幅
- **端口**：22
- **提取**：SSH 版本串与厂商提示。
- **示例**
  ```
  SSH-2.0-Cisco-1.25  # 识别为 Cisco 设备
  SSH-2.0-OpenSSH_7.9 # 典型 Linux/Unix 主机
  ```

### 打印机协议
- **IPP (631)**：Get-Printer-Attributes → 型号、厂商
- **LPD (515)**：作业握手用于检测打印机服务

### IoT 协议
- **CoAP (5683)**：GET `/.well-known/core` → 资源列表与设备线索

## 识别优先级
主动探测结果置信度最高（75–85%），因为数据直接来自设备：
1. 主动探测（HTTP/Telnet/SSH/打印/IoT）
2. 本地 OUI 与关键字/词典匹配（约 80%）
3. DHCP 指纹（本地，约 70%）

## 配置
- 通过环境变量启用/禁用：
  ```bash
  FEATURE_ACTIVE_PROBE=true   # 默认
  FEATURE_ACTIVE_PROBE=false  # 禁用主动探测
  ```
- 超时：单次探测约 2 秒，每台设备整体约 3 秒（端口不可用时快速跳过）。

## 提取数据示例
### HTTP 响应
```json
{
  "http_server": "TP-Link Router",
  "http_title": "TP-Link Router Admin - TL-WR940N",
  "http_port": 80,
  "http_status": 200
}
```

### Telnet 横幅
```json
{
  "telnet_banner": "Welcome to TP-Link Router\nModel: TL-WR940N"
}
```

### SSH 横幅
```json
{
  "ssh_banner": "SSH-2.0-Cisco-1.25",
  "ssh_vendor": "Cisco"
}
```

### 识别结果示例
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

## 安全性
- 只读操作：仅 GET 和横幅读取，不修改设备状态。
- 超时限制：每个探测有超时，避免长时间阻塞。
- 并发受控：并行探测，但每台设备的并发和超时均受控。
- 错误隔离：失败会被捕获，不影响其他探测。

## 性能
- 并行探测多个端口/协议。
- 端口不可达时快速失败并切换。
- 典型单设备耗时约 2–3 秒（取决于设备响应）。

## 常见设备
- **路由器**：Web UI (80/443)，部分有 Telnet (23)；从标题与 Server 头提取厂商/型号。
- **打印机**：IPP (631) 与 LPD (515)；从 IPP 属性提取型号。
- **IoT 设备**：Web UI 或 CoAP (5683)；从 HTTP/CoAP 响应提取型号。
- **服务器/PC**：SSH (22) 和 HTTP (80/443)；从横幅获取操作系统/厂商线索。

## 故障排查
- 可能原因：防火墙阻断、端口未开放、需要认证 (401/403)、超时过短。
- 提升成功率：适当增加超时、确认开放端口、查看 `active_probe` 相关日志。

## 与其他方法结合
主动探测与 mDNS、SSDP/UPnP、本地 OUI 与词典结果一起使用，结果会加权合并以确定最终识别。

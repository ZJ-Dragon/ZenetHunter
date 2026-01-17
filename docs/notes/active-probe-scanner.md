# Active Probe Scanner Implementation Plan

## 目标
将设备扫描从"被动读取 ARP 表"升级为"主动探测"，实现 Stage A (Discovery) + Stage B (Fingerprint Enrichment)。

## 子任务清单

1. **Refactor: 抽象扫描 pipeline**
   - 创建 `scanner/pipeline.py` 编排 Stage A + Stage B
   - 创建 `scanner/capabilities.py` 权限/能力探测
   - 添加配置项（SCAN_RANGE, SCAN_TIMEOUT_SEC, SCAN_CONCURRENCY）

2. **Discovery-ARP: 实现 ARP sweep**
   - 创建 `scanner/discovery/arp_sweep.py`
   - 实现主动 ARP 探测（不依赖陈旧 ARP 表）
   - 结果入库并发 WebSocket 事件

3. **Remove Legacy: 删除旧实现**
   - 删除 `_scan_arp_table` 等被动读取 ARP 表的方法
   - 清理相关配置和测试

4. **Enrich-mDNS: 实现 mDNS enrichment**
   - 创建 `scanner/enrich/mdns.py`
   - 写入 fingerprint，触发识别更新

5. **Enrich-SSDP: 实现 SSDP enrichment**
   - 创建 `scanner/enrich/ssdp.py`
   - 同上

6. **Recognition Glue: 证据融合**
   - 更新 recognition_engine 融合 enrichment 证据
   - API 输出对齐

7. **Hardening: 限速/并发/超时**
   - 实现限速和并发控制
   - 错误处理和审计日志

8. **Config: 添加配置项和 feature flags**
   - 在 settings 页面添加开关控件
   - FEATURE_MDNS, FEATURE_SSDP, FEATURE_NBNS, FEATURE_SNMP, FEATURE_FINGERBANK

9. **Final: 全量检查**
   - pre-commit run --all-files
   - pytest
   - CI 检查

## 验收标准
- 手动触发 POST /api/scan/start：能发现设备（不依赖陈旧 ARP 表）
- 至少 mDNS 或 SSDP 有一个 enrichment 能产出证据链
- 识别结果出现 vendor/model guess + confidence + evidence
- 默认配置不外联、低侵入、可降级、CI 全绿

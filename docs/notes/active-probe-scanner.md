# Active Probe Scanner - Task List

## 目标
将扫描系统从被动读取 ARP 表升级为主动探测 + 指纹增强。

## 子任务清单

### Phase 1: 基础架构重构
- [ ] 1. 抽象扫描 pipeline（Stage A/B），引入能力探测与配置
- [ ] 2. 实现 ARP sweep（或等价主动发现方式），结果入库并发 WS
- [ ] 3. 删除旧"读 ARP 表"扫描路径与相关配置/测试

### Phase 2: 指纹增强
- [ ] 4. 实现 mDNS enrichment → 写 fingerprint → 触发识别更新
- [ ] 5. 实现 SSDP enrichment → 同上

### Phase 3: 识别与UI对齐
- [ ] 6. 证据融合（confidence + evidence），API 输出对齐
- [ ] 7. UI 展示 evidence / confidence 更新（最小改动）

### Phase 4: 加固与测试
- [ ] 8. 限速/并发/超时、错误路径、审计日志补全
- [ ] 9. 全面检查前后端对齐/UI 展示 + 全量 pre-commit + tests + 修 CI

## 验收标准
- 手动触发 POST /api/scan/start 能发现设备（不依赖陈旧 ARP 表）
- 至少 mDNS 或 SSDP 有一个 enrichment 能产出证据链
- 识别结果出现 vendor/model guess + confidence + evidence
- 默认配置不外联、低侵入、可降级、CI 全绿

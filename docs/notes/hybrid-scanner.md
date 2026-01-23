# 混合扫描机制实现计划

## 目标

实现"候选集驱动"的混合扫描，替代全网段扫描，降低资源占用。

## 架构设计

### 三阶段扫描流程

```
┌─────────────┐
│ 1. Candidate│ 从缓存/租约获取候选集
│   Generator │ (ARP cache, DHCP leases)
└──────┬──────┘
       │ 候选列表 (IP/MAC pairs)
       ↓
┌─────────────┐
│ 2. Refresh  │ 定向探测确认在线状态
│   Prober    │ (限速, 短窗口)
└──────┬──────┘
       │ 在线设备列表
       ↓
┌─────────────┐
│ 3. Enrich   │ 采集设备特征/指纹
│   Collector │ (mDNS, SSDP, DHCP)
└──────┬──────┘
       │ 完整设备信息 + 识别结果
       ↓
  Device DB + WS Events
```

## 子任务清单

### Phase 1: 候选集生成（2个子任务）

- [ ] **Task 1.1**: 实现 ARP/邻居缓存读取器
  - 文件: `backend/app/services/scanner/candidate/arp_cache.py`
  - 功能: 读取系统ARP表（Linux/macOS/Windows）
  - 返回: `[(ip, mac, last_seen)]`
  - 测试: 单元测试验证各平台

- [ ] **Task 1.2**: 实现 DHCP租约读取器
  - 文件: `backend/app/services/scanner/candidate/dhcp_leases.py`
  - 功能: 读取DHCP租约文件（如果可用）
  - 返回: `[(ip, mac, hostname, lease_time)]`
  - 测试: 模拟租约文件测试

### Phase 2: 刷新器（2个子任务）

- [ ] **Task 2.1**: 实现候选刷新探测器
  - 文件: `backend/app/services/scanner/refresh/prober.py`
  - 功能: 定向ping/ARP探测候选设备
  - 限速: 10个并发，1秒超时
  - 返回: `[(ip, mac, online: bool, rtt)]`

- [ ] **Task 2.2**: 添加刷新窗口配置和超时控制
  - 配置: `SCAN_REFRESH_WINDOW=10s`
  - 配置: `SCAN_REFRESH_CONCURRENCY=10`
  - 功能: 超时自动跳过，不阻塞

### Phase 3: Pipeline重构（3个子任务）

- [ ] **Task 3.1**: 重构pipeline三阶段编排
  - 文件: `backend/app/services/scanner/pipeline.py`
  - 流程: candidate → refresh → enrich
  - 事件: 每阶段完成发送WS事件

- [ ] **Task 3.2**: 更新scanner_service集成三阶段
  - 文件: `backend/app/services/scanner_service.py`
  - 流程: 调用pipeline，处理结果
  - 日志: 每步输出succeed字段

- [ ] **Task 3.3**: 添加扫描来源标记
  - DB字段: `discovery_source` (candidate-cache/dhcp/active-refresh/enrich)
  - 字段: `freshness_score` (0-100)
  - 更新: Device模型和数据库schema

### Phase 4: Enrich优化（1个子任务）

- [ ] **Task 4.1**: Enrich仅对confirmed-online执行
  - 修改: `scanner/enrich/*.py`
  - 逻辑: 检查设备在线状态
  - 限速: 严格并发控制

### Phase 5: 配置与UI（2个子任务）

- [ ] **Task 5.1**: 添加扫描模式配置
  - 配置: `SCAN_MODE=hybrid|full`（默认hybrid）
  - 配置: `SCAN_ALLOW_FULL_SUBNET=false`
  - UI: Settings中添加高级扫描选项

- [ ] **Task 5.2**: 更新WebSocket事件
  - 新增: `scanProgress` (候选数/刷新数/enrich数)
  - 新增: `deviceRecognitionUpdated`
  - 更新: `scanCompleted` 包含统计

### Phase 6: 测试与文档（2个子任务）

- [ ] **Task 6.1**: Pre-commit + 单元测试
  - 运行: `pre-commit run --all-files`
  - 运行: `pytest backend/tests/`
  - 修复: 所有错误

- [ ] **Task 6.2**: 更新文档
  - 文档: `docs/guides/HYBRID_SCAN.md`
  - 更新: API文档
  - 示例: 端到端验证记录

---

## 总计: 12个子任务

预计时间: 每个子任务15-30分钟，总计3-6小时

## 验收标准

- ✅ 默认扫描不扫全网段
- ✅ 候选集从缓存/租约生成
- ✅ 刷新阶段确认在线
- ✅ Enrich仅对在线设备
- ✅ 所有阶段有超时和限速
- ✅ WebSocket事件完整
- ✅ 日志包含succeed字段
- ✅ Pre-commit通过
- ✅ 测试通过

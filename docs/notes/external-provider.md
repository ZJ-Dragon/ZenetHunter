# 外部识别Provider实现计划

## 目标

在不泄露隐私、不增加滥用风险的前提下，通过公共API提升设备识别准确率。

## 核心原则

1. **默认不外联**: FEATURE_EXTERNAL_LOOKUP=false
2. **最小化数据**: 仅发送必要信息（优先OUI前缀）
3. **严格限流**: 遵守provider限制
4. **强缓存**: 避免重复请求
5. **完整审计**: 记录所有外联（脱敏）

---

## 子任务清单（10个任务）

### Phase 1: 基础架构 (4个任务)

- [ ] **Task 1.1**: Provider接口定义
  - 文件: `backend/app/services/recognition/providers/base.py`
  - 接口: `lookup_vendor()`, `lookup_device()`
  - 返回: 统一的Provider结果格式

- [ ] **Task 1.2**: HTTP客户端（安全策略）
  - 文件: `backend/app/services/recognition/providers/http_client.py`
  - 功能: 域名白名单、超时、重试、限流、熔断
  - 配置: `ALLOWED_EXTERNAL_DOMAINS`

- [ ] **Task 1.3**: 缓存层（TTL + LRU）
  - 文件: `backend/app/services/recognition/providers/cache.py`
  - 功能: 本地文件缓存，LRU淘汰
  - TTL: 7天
  - 位置: `backend/.cache/recognition/` (加入.gitignore)

- [ ] **Task 1.4**: 外联策略配置
  - 文件: `backend/app/services/recognition/external_service_policy.py`
  - 功能: 集中配置（开关、白名单、限流、脱敏）
  - 配置: `FEATURE_EXTERNAL_LOOKUP=false`

### Phase 2: MACVendors Provider (3个任务)

- [ ] **Task 2.1**: MACVendors无密钥provider
  - 文件: `backend/app/services/recognition/providers/macvendors.py`
  - API: https://api.macvendors.com/{oui}
  - 限制: 1000 requests/day, 2 requests/second
  - 模式: 只发OUI（前24位）

- [ ] **Task 2.2**: 集成到识别引擎
  - 文件: `backend/app/services/recognition_engine.py`
  - 优先级: 本地证据 → MACVendors → 本地默认
  - Evidence: 标注来源 `external:macvendors`

- [ ] **Task 2.3**: 单元测试
  - 文件: `backend/tests/test_macvendors_provider.py`
  - 测试: 缓存命中、限流、超时、域名白名单

### Phase 3: UI与API (2个任务)

- [ ] **Task 3.1**: Settings API
  - 端点: `GET/POST /api/settings/external-lookup`
  - 端点: `GET /api/recognition/providers`
  - 功能: 开启/关闭外联，查询provider状态

- [ ] **Task 3.2**: Settings UI开关
  - 页面: Settings → External Services
  - 显示: 隐私提示、发送字段说明
  - 控件: 开关 + 警告框

### Phase 4: 文档与审计 (1个任务)

- [ ] **Task 4.1**: 完善文档
  - `PRIVACY.md`: 外联隐私说明
  - `EXTERNAL_SERVICES.md`: Provider说明
  - `SECURITY.md`: 更新安全策略

---

## 总计: 10个子任务

预计时间: 3-5小时

---

## 实现检查点

每完成2-3个任务后运行：
```bash
pre-commit run --all-files
pytest backend/tests/
```

---

## 验收标准

1. ✅ 默认配置不外联
2. ✅ MACVendors仅发OUI前缀
3. ✅ 缓存命中不重复请求
4. ✅ 超限返回错误不崩溃
5. ✅ 审计日志脱敏
6. ✅ UI有明确隐私提示
7. ✅ 文档说明默认行为

# 主动探测可观测性

可观测性为探测/富化返回值提供可复现轨迹，同时避免存储原始包体。

## 数据流
1. 探测/富化模块返回结构化线索（HTTP 标题/Server，SSDP 设备信息，mDNS 服务名，精简 banner 等）。
2. 观测管线对关键字段做白名单筛选与脱敏，提取关键词，生成摘要，并写入 SQLite 表 `probe_observations`。
3. 事件日志在上下文中引用 observation_id，便于追溯。
4. API 提供只读视图供前端展示与导出。

## 存储结构
- 表：`probe_observations`
  - `id` (UUID)、`device_mac`、`scan_run_id`、`protocol`、`timestamp`
  - `key_fields`（JSON）、`keywords`（JSON 数组）、`keyword_hits`（JSON 数组）、`raw_summary`（TEXT）、`redaction_level`（TEXT）
- 本地默认 SQLite 路径：`./data/zenethunter.db`（WAL/SHM 位于同目录）。
- WAL/SHM 不入库；复制 SQLite 文件 + NDJSON 导出即可离线复现。

## API
- `GET /api/devices/{mac}/observations?limit=&since=&format=ndjson|json`
- `GET /api/scan/{scan_run_id}/observations`
- NDJSON 导出可追加、便于回放和外部分析。

## 前端体验
- 拓扑详情抽屉：“Probe Details / Observations”（默认折叠）。摘要显示协议/时间/关键词数，展开后展示 key_fields 和 keywords，并支持复制/导出。
- 设备列表：每行“更多”省略号按钮展开紧凑观测预览，并显示关键词命中数。
- 拓扑详情同时提供 “Keyword Intelligence” 卡片（默认折叠）：抬头展示命中数量与最高优先级推断摘要，展开后列出命中关键词、说明、置信度增量与推断字段（vendor/product/os/category）。

## 关键词提取与词典
- 关键词来源于关键字段的规范化 token。
- 词典文件 `backend/app/data/keyword_dictionary.yaml`（版本化 YAML）：
  - 顶层：`version`、`updated`、`rules[]`
  - 规则：`id`、`priority`、`match.any_contains[]`（小写）、可选 `match.any_regex[]`（仅用于少量精确规则）、`infer.vendor/product/category/os`、`confidence_delta`（整数）、`notes`（一句话）。
  - 命中：`rule_id`、`matched_token`、`infer` + `infer_summary`、`confidence_delta`、`priority`、`notes`。同一观测重复命中同一规则会去重。
- 优先级与置信度：优先级高的规则先应用；delta 累加后裁剪到 0–100。
- 加载行为：词典缺失或无效时会记录清晰错误并退回“无词典模式”（不产生命中/增量）。

## 复现路径
- 运行扫描后，通过设备或 `scan_run_id` 拉取观测数据。
- 导出 NDJSON 并保存 SQLite 文件，即可重放同一批观测。

## 操作提示
- 保持日志简洁，避免直接输出原始响应。
- 新增富化模块时务必走观测管线（脱敏 → 关键词 → 摘要 → 存储）。

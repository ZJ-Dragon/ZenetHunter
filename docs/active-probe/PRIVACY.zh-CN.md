# 主动探测隐私与脱敏策略

本项目在授权环境下记录探测观测数据，严格避免把敏感包体写入持久化存储或日志。

## 存储内容
- **关键字段**：仅保存白名单中的短字符串（如 `http_title`、`http_server`、SSDP 厂商/型号提示、短 banner、mDNS 服务名）。
- **关键词**：从关键字段提取、规范化的 token，以及词典命中的 **keyword_hits**（规则 ID、匹配 token、推断摘要、置信度增量）。
- **摘要**：简短可读描述，不含原始载荷。
- **元数据**：协议/模块名、设备 MAC、可选 `scan_run_id`、时间戳、脱敏级别。

## 不存储的内容
- 完整包体或二进制数据。
- 凭证、cookie、token 等敏感标识。
- 白名单以外的自由文本/字段。

## 脱敏与清洗
- 字符串去空白、去换行、HTML 转义并截断（通常 ≤160 字符）。
- 仅持久化白名单字段，其余全部丢弃。
- 结构化日志只记录摘要，详细字段仅留在观测存储。
- 词典文件 `backend/app/data/keyword_dictionary.yaml` 随代码版本化，命中结果以 `keyword_hits` 存储（rule id、匹配 token、置信度增量与推断），不含原始包体。

## 导出与复现
- 观测数据支持 NDJSON 导出（一行一条 JSON）。
- 导出内容只包含上述脱敏字段，便于离线分析与复现。

## 关键词词典
- 版本化 YAML：`backend/app/data/keyword_dictionary.yaml`（git 跟踪，仅包含非敏感关键词）。
- Schema：`version`、`updated`、`rules[]`（id、priority、match.any_contains/any_regex、infer.vendor/product/category/os、confidence_delta、notes）。
- 加载器在启动时校验文件；若缺失或格式错误，会记录清晰错误并退回“无词典模式”（不产生命中、不调整置信度）。
- 命中记录仅含规则 ID、匹配 token、推断摘要与 delta，不包含原始包体。

## 使用建议
- 仅在授权、可控网络环境中运行探测。
- 对外分享前请先审阅导出内容。
- 新增探测/富化模块时，务必只写入已脱敏的关键字段，避免持久化原始包体。

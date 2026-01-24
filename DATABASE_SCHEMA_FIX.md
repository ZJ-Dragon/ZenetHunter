# 数据库Schema快速修复

## 问题

```
OperationalError: no such column: devices.discovery_source
OperationalError: no such column: devices.freshness_score
```

## 解决方案

### 方式1: 一键修复（推荐）

```bash
# 停止服务
^C

# 添加缺失的列
sqlite3 backend/data/zenethunter.db <<EOF
ALTER TABLE devices ADD COLUMN discovery_source TEXT DEFAULT NULL;
ALTER TABLE devices ADD COLUMN freshness_score INTEGER DEFAULT NULL;
EOF

# 重启服务
./start-local.sh
```

### 方式2: 删除数据库重建

```bash
# 停止服务
^C

# 删除旧数据库
rm -rf backend/data/*.db*

# 重启（自动创建新schema）
./start-local.sh
```

---

## ✅ 已执行

列已成功添加到数据库：
```
20|discovery_source|TEXT|0|NULL|0
21|freshness_score|INTEGER|0|NULL|0
```

## 下一步

**重启后端服务**：
```bash
./cleanup.sh  # 清理旧进程
./start-local.sh  # 重新启动
```

然后测试扫描功能。

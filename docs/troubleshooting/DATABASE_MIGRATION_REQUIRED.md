# 🚨 数据库迁移必需通知

## 问题

```
sqlite3.OperationalError: no such column: devices.active_defense_status
```

## 原因

数据库schema与代码不匹配：
- **旧schema**: 有 `attack_status`、`defense_status`、`active_defense_policy` 列
- **新schema**: 只有 `active_defense_status` 列

## 解决方案

### 方案1: 运行Alembic迁移（推荐）

```bash
cd /Volumes/MobileWorkstation/Projects/ZenetHunter/backend
alembic upgrade head
```

### 方案2: 删除旧数据库并重建

```bash
# 停止后端
^C

# 删除旧数据库
rm -rf backend/data/*.db backend/data/*.db-*

# 重新启动（会自动创建新数据库）
./start-local.sh
```

### 方案3: 手动添加列（临时）

```bash
sqlite3 backend/data/zenethunter.db <<EOF
ALTER TABLE devices ADD COLUMN active_defense_status TEXT DEFAULT 'idle';
ALTER TABLE devices ADD COLUMN recognition_manual_override BOOLEAN DEFAULT 0;
UPDATE devices SET active_defense_status = attack_status WHERE active_defense_status IS NULL;
EOF
```

## 已集成自动迁移到启动脚本

start-local.sh 已更新，会自动处理数据库迁移。

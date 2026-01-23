# 环境配置指南

## 智能环境检测

start-local.sh 现在会自动检测并适配您的Python环境类型，确保不污染系统环境。

---

## 🎯 支持的环境类型

### 1. Conda环境（推荐）✨

**检测条件**: `$CONDA_DEFAULT_ENV` 已设置且不是 `base`

**行为**:
- ✅ 自动使用当前conda环境
- ✅ 通过pip安装依赖到conda环境
- ✅ 不创建.venv目录
- ✅ 完全隔离，不污染任何环境

**使用方式**:
```bash
# 创建并激活conda环境
conda env create -f environment.yml
conda activate zenethunter

# 启动服务（自动检测conda环境）
./start-local.sh

# 输出示例:
# ✓ 检测到 Conda 环境: zenethunter
# ✅ 依赖已安装到 Conda 环境: zenethunter
```

### 2. Python虚拟环境（venv）

**检测条件**: `$VIRTUAL_ENV` 已设置 或 `.venv` 目录存在

**行为**:
- ✅ 使用现有venv
- ✅ 或自动激活本地.venv
- ✅ 隔离的Python环境

**使用方式**:
```bash
# 手动创建venv
python3 -m venv .venv
source .venv/bin/activate

# 启动服务
./start-local.sh

# 或让脚本自动处理
./start-local.sh  # 发现.venv会自动激活
```

### 3. 系统环境（不推荐）⚠️

**检测条件**: 无虚拟环境且用户确认

**行为**:
- ⚠️ 警告用户可能污染系统环境
- ⚠️ 要求确认后才继续
- ⚠️ 安装到全局Python环境

**使用方式**:
```bash
./start-local.sh

# 会提示:
# 未检测到虚拟环境
# 是否在系统环境中继续？(y/n)
```

---

## 🚀 推荐工作流

### Conda用户（最佳实践）

```bash
# 1. 克隆仓库
git clone <repo>
cd ZenetHunter

# 2. 创建conda环境（一次性）
conda env create -f environment.yml

# 3. 每次使用时
conda activate zenethunter
./start-local.sh

# ✅ 完全隔离，零污染
```

### pip/venv用户

```bash
# 1. 克隆仓库
git clone <repo>
cd ZenetHunter

# 2. 创建虚拟环境（一次性）
python3 -m venv .venv

# 3. 每次使用时
source .venv/bin/activate
./start-local.sh

# ✅ 隔离环境，推荐方式
```

---

## 🔍 环境检测逻辑

### 检测流程

```bash
1. 检查 $CONDA_DEFAULT_ENV
   ├─ 存在且不是"base" → 使用Conda环境 ✅
   └─ 不存在 → 继续检查

2. 检查 $VIRTUAL_ENV
   ├─ 存在 → 使用venv环境 ✅
   └─ 不存在 → 继续检查

3. 检查 .venv 目录
   ├─ 存在 → 激活并使用 ✅
   └─ 不存在 → 提示用户

4. 无环境
   └─ 警告并询问确认 ⚠️
```

### 环境优先级

```
Conda环境 > venv环境 > .venv目录 > 系统环境(需确认)
```

---

## 📊 安装行为对比

| 环境类型 | 检测变量 | 安装位置 | 污染风险 |
|----------|---------|----------|----------|
| Conda环境 | `$CONDA_DEFAULT_ENV` | Conda env | ✅ 无 |
| venv环境 | `$VIRTUAL_ENV` | .venv/ | ✅ 无 |
| 系统环境 | (无) | 全局Python | ❌ 高 |

---

## 🎨 启动输出示例

### 场景1: Conda环境

```bash
$ conda activate zenethunter
$ ./start-local.sh

=== ZenetHunter 本地启动 ===

✓ 检测到 Conda 环境: zenethunter
  将使用当前 Conda 环境安装依赖

安装/更新依赖...
使用 Conda 环境安装依赖...
✅ 依赖已安装到 Conda 环境: zenethunter

检查数据库状态...
✅ 数据库schema正常

✅ 后端服务器已启动 (PID: 12345)
```

### 场景2: venv环境

```bash
$ source .venv/bin/activate
$ ./start-local.sh

=== ZenetHunter 本地启动 ===

✓ 检测到虚拟环境: /path/to/.venv

安装/更新依赖...
使用虚拟环境安装依赖...
✅ 依赖已安装到虚拟环境
```

### 场景3: 无环境（首次运行）

```bash
$ ./start-local.sh

=== ZenetHunter 本地启动 ===

未检测到虚拟环境

建议使用隔离环境运行，避免污染系统环境：

选项1（推荐）: Conda环境
  conda env create -f ../environment.yml
  conda activate zenethunter
  ./start-local.sh

选项2: Python虚拟环境
  python3 -m venv .venv
  source .venv/bin/activate
  ./start-local.sh

选项3: 使用系统环境（不推荐）
  继续运行（可能污染系统Python环境）

是否在系统环境中继续？(y/n) n
已取消。请先创建虚拟环境或conda环境
```

---

## ⚙️ 技术实现

### 环境检测代码

```bash
# 检测Conda环境
if [ ! -z "$CONDA_DEFAULT_ENV" ] && [ "$CONDA_DEFAULT_ENV" != "base" ]; then
    IN_CONDA=true
    echo "✓ 检测到 Conda 环境: $CONDA_DEFAULT_ENV"
fi

# 检测venv环境
if [ ! -z "$VIRTUAL_ENV" ]; then
    IN_VENV=true
    echo "✓ 检测到虚拟环境: $VIRTUAL_ENV"
fi

# 查找本地.venv
if [ -d ".venv" ]; then
    source .venv/bin/activate
    IN_VENV=true
fi
```

### 安装逻辑

```bash
if [ "$IN_CONDA" = true ]; then
    # Conda环境：使用pip安装到conda env
    pip install -e .
    echo "✅ 安装到 Conda 环境: $CONDA_DEFAULT_ENV"

elif [ "$IN_VENV" = true ]; then
    # venv环境：正常pip安装
    pip install -e .
    echo "✅ 安装到虚拟环境"

else
    # 系统环境：警告后安装
    echo "⚠️  安装到系统环境"
fi
```

---

## 🛡️ 安全防护

### 防止污染系统环境

1. **强制隔离检查**
   - ✅ 未检测到任何虚拟环境时
   - ✅ 显示详细的环境创建说明
   - ✅ 要求用户明确确认

2. **清晰的警告**
   - ⚠️ 红色警告文字
   - ⚠️ 明确说明风险
   - ⚠️ 提供替代方案

3. **conda base保护**
   - ✅ 检测到base环境视为"无环境"
   - ✅ 要求创建专用环境
   - ✅ 防止污染conda base

---

## 🎯 最佳实践

### 开发环境

**推荐使用Conda**:
```bash
conda env create -f environment.yml
conda activate zenethunter
./start-local.sh
```

**优势**:
- ✅ 依赖管理更强大
- ✅ 包含非Python依赖（libpcap等）
- ✅ 跨平台一致性好
- ✅ 环境切换方便

### CI/CD环境

**使用requirements.txt**:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd backend && pip install -e .
```

**优势**:
- ✅ 轻量级
- ✅ Docker友好
- ✅ 安装快速

---

## 📋 对比表

| 特性 | Conda | venv | 系统环境 |
|------|-------|------|----------|
| 隔离性 | ✅ 优秀 | ✅ 良好 | ❌ 无 |
| 依赖管理 | ✅ 强大 | ⚠️ 基本 | ❌ 混乱 |
| 跨平台 | ✅ 一致 | ⚠️ 可能差异 | ❌ 不可控 |
| 安装速度 | ⚠️ 较慢 | ✅ 快 | ✅ 快 |
| 磁盘占用 | ⚠️ 大 | ✅ 小 | ✅ 无额外 |
| 推荐度 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐ |

---

## Git提交

```bash
94e04a3 feat: auto-detect conda env and prevent system pollution
```

---

## ✅ 功能完成

**智能检测**: ✅ Conda/venv/系统环境  
**防污染**: ✅ 强制确认机制  
**用户友好**: ✅ 清晰的提示和建议  
**文档完整**: ✅ 使用指南

---

**建议**: 使用 `conda env create -f environment.yml` 获得最佳体验！

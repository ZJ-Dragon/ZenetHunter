# IDE 导入错误修复指南

## 🐛 问题

IDE显示导入错误：
- ❌ 无法解析导入 "pydantic"
- ❌ 无法解析导入 "fastapi"  
- ❌ 无法解析导入 "scapy.all"

## 原因

IDE的Python解释器未指向正确的虚拟环境，或依赖未安装。

---

## ✅ 快速修复

### 步骤1: 安装所有依赖

```bash
cd /Volumes/MobileWorkstation/Projects/ZenetHunter

# 方式1: 使用Conda（推荐）
conda env create -f environment.yml
conda activate zenethunter
cd backend && pip install -e . && cd ..

# 方式2: 使用venv
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
cd ..

# 方式3: 直接安装到当前环境
pip install -r requirements.txt
cd backend && pip install -e .
```

### 步骤2: 配置IDE Python解释器

#### VSCode

1. 打开命令面板 (Cmd+Shift+P)
2. 输入 "Python: Select Interpreter"
3. 选择：
   - Conda: `~/miniconda3/envs/zenethunter/bin/python`
   - venv: `./backend/.venv/bin/python`

#### PyCharm

1. Preferences → Project → Python Interpreter
2. 点击齿轮 → Add
3. 选择：
   - Conda Environment → 选择 zenethunter
   - Virtualenv Environment → 选择 backend/.venv

#### Cursor

1. 打开命令面板
2. "Python: Select Interpreter"
3. 选择虚拟环境

### 步骤3: 重启IDE

```bash
# 重启后IDE应该能识别所有导入
```

---

## 🔍 验证安装

```bash
# 激活环境
conda activate zenethunter
# 或
source backend/.venv/bin/activate

# 验证导入
python3 << EOF
import pydantic
import fastapi
import scapy.all
import sqlalchemy
print("✅ 所有依赖正常导入")
print(f"Pydantic: {pydantic.__version__}")
print(f"FastAPI: {fastapi.__version__}")
print(f"Scapy: {scapy.__version__}")
print(f"SQLAlchemy: {sqlalchemy.__version__}")
EOF
```

---

## 📦 完整依赖列表

### 核心依赖（必需）
```
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
pydantic>=2.0
pydantic-settings>=2.0
sqlalchemy>=2.0
greenlet>=3.0.0
aiosqlite>=0.19.0
alembic>=1.13.0
scapy>=2.5.0
pyjwt>=2.8.0
python-multipart>=0.0.6
```

### 开发工具
```
pytest>=7.0
httpx>=0.24.0
ruff
black
pre-commit
```

---

## 🚀 一键修复脚本

创建并运行：
```bash
cat > fix-imports.sh << 'EOF'
#!/bin/bash
cd backend

# 检查是否在虚拟环境中
if [ -z "$VIRTUAL_ENV" ] && [ -z "$CONDA_DEFAULT_ENV" ]; then
    # 创建venv
    python3 -m venv .venv
    source .venv/bin/activate
fi

# 安装所有依赖
pip install --upgrade pip
pip install -e .

echo "✅ 依赖安装完成"
echo "请重启IDE并选择解释器："
echo "  路径: $(which python)"
EOF

chmod +x fix-imports.sh
./fix-imports.sh
```

---

## Git提交

```bash
9c61ab2 docs: add complete port occupation fix guide
```

---

**状态**: ✅ **解决方案已提供**  
**下一步**: 运行 `./cleanup.sh` 然后 `./start-local.sh`

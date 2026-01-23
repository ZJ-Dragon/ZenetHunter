# Conda 环境配置指南

## 快速开始

### 使用 Conda 创建环境

```bash
# 1. 创建环境
conda env create -f environment.yml

# 2. 激活环境
conda activate zenethunter

# 3. 安装后端包
cd backend
pip install -e .

# 4. 运行数据库迁移
alembic upgrade head

# 5. 启动服务
cd ..
./start-local.sh
```

---

## 环境管理

### 创建环境

```bash
conda env create -f environment.yml
```

### 更新环境

```bash
conda env update -f environment.yml --prune
```

### 激活/停用

```bash
# 激活
conda activate zenethunter

# 停用
conda deactivate
```

### 删除环境

```bash
conda env remove -n zenethunter
```

---

## 依赖说明

### Python版本

- **要求**: Python >=3.11, <3.13
- **推荐**: Python 3.12

### 核心依赖

| 包名 | 版本 | 用途 |
|------|------|------|
| fastapi | >=0.104.0 | Web框架 |
| uvicorn | >=0.24.0 | ASGI服务器 |
| sqlalchemy | >=2.0 | 数据库ORM |
| scapy | >=2.5.0 | 网络包操作 |
| alembic | >=1.13.0 | 数据库迁移 |
| pyjwt | >=2.8.0 | JWT认证 |

### 开发工具

| 包名 | 用途 |
|------|------|
| pytest | 测试框架 |
| ruff | 快速linter |
| black | 代码格式化 |
| pre-commit | Git钩子 |
| ipython | 交互式Shell |

---

## 与 pip/venv 的区别

### Conda方式

**优点**:
- ✅ 更好的依赖解析
- ✅ 包含非Python依赖（如libpcap for scapy）
- ✅ 环境隔离更彻底
- ✅ 跨平台更一致

**缺点**:
- ⚠️ 首次安装较慢
- ⚠️ 环境体积较大

### pip/venv方式

**优点**:
- ✅ 安装快速
- ✅ 环境体积小
- ✅ 使用熟悉的pip

**缺点**:
- ⚠️ 需要手动安装系统依赖
- ⚠️ macOS/Linux可能需要编译某些包

---

## 平台特定说明

### macOS

```bash
# 创建环境
conda env create -f environment.yml

# Scapy需要root权限
sudo conda activate zenethunter  # 不推荐
# 或
conda activate zenethunter
sudo $(which python) -m uvicorn app.main:app  # 使用conda的python
```

### Linux

```bash
# 创建环境
conda env create -f environment.yml

# 方式1: Root权限
conda activate zenethunter
sudo ./start-local.sh

# 方式2: CAP_NET_RAW capability
conda activate zenethunter
sudo setcap cap_net_raw+ep $(which python)
./start-local.sh
```

### Windows

```bash
# 创建环境（需要管理员权限打开Anaconda Prompt）
conda env create -f environment.yml

# 安装Npcap（Scapy依赖）
# 下载: https://npcap.com/

# 激活并运行（需要管理员权限）
conda activate zenethunter
cd backend
python -m uvicorn app.main:app --reload
```

---

## 验证安装

### 检查Python版本

```bash
conda activate zenethunter
python --version
# 应该显示: Python 3.11.x or 3.12.x
```

### 检查关键依赖

```bash
python -c "
import fastapi
import uvicorn
import sqlalchemy
import scapy
print('✅ All core dependencies installed')
print(f'FastAPI: {fastapi.__version__}')
print(f'SQLAlchemy: {sqlalchemy.__version__}')
print(f'Scapy: {scapy.__version__}')
"
```

### 检查导入

```bash
cd backend
python -c "
from app.main import app
print('✅ Backend imports successful')
"
```

---

## 故障排除

### 问题1: Scapy安装失败

**症状**:
```
ERROR: Could not build wheels for scapy
```

**解决方案**:
```bash
# macOS
brew install libpcap
conda install -c conda-forge scapy

# Linux
sudo apt-get install libpcap-dev
conda install -c conda-forge scapy

# Windows
# 先安装 Npcap: https://npcap.com/
conda install -c conda-forge scapy
```

### 问题2: 环境创建慢

**解决方案**:
```bash
# 使用mamba（更快的conda替代）
conda install -n base conda-forge::mamba
mamba env create -f environment.yml
```

### 问题3: 依赖冲突

**解决方案**:
```bash
# 清理conda缓存
conda clean --all

# 重新创建环境
conda env remove -n zenethunter
conda env create -f environment.yml
```

---

## 导出环境

### 导出当前环境

```bash
# 精确版本（可重现）
conda env export > environment-lock.yml

# 无版本号（灵活）
conda env export --from-history > environment.yml
```

### 分享环境

```bash
# 其他用户使用
conda env create -f environment-lock.yml
```

---

## 性能优化

### 使用 Mamba

```bash
# 安装mamba
conda install -n base -c conda-forge mamba

# 使用mamba创建环境（快5-10倍）
mamba env create -f environment.yml
```

### 使用国内镜像

```bash
# 添加清华镜像
conda config --add channels https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/free/
conda config --add channels https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/main/
conda config --add channels https://mirrors.tuna.tsinghua.edu.cn/anaconda/cloud/conda-forge/

# 创建环境
conda env create -f environment.yml
```

---

## 与requirements.txt对比

| 文件 | 用途 | 工具 |
|------|------|------|
| `environment.yml` | Conda环境 | conda/mamba |
| `requirements.txt` | pip安装 | pip/venv |
| `backend/pyproject.toml` | 包元数据 | setuptools |

**建议**:
- **开发环境**: 使用 environment.yml（更完整）
- **生产环境**: 使用 requirements.txt（Docker友好）
- **快速测试**: 使用 pip install -e backend/

---

## 示例工作流

### 开发者A（使用conda）

```bash
git clone <repo>
cd ZenetHunter
conda env create -f environment.yml
conda activate zenethunter
cd backend && pip install -e . && cd ..
./start-local.sh
```

### 开发者B（使用venv）

```bash
git clone <repo>
cd ZenetHunter
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd backend && pip install -e . && cd ..
./start-local.sh
```

---

**文档版本**: 1.0  
**Python要求**: >=3.11, <3.13  
**推荐Conda版本**: >=23.0 or mamba >=1.0

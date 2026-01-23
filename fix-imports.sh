#!/bin/bash
echo "=== 修复IDE导入错误 ==="
cd backend

if [ -z "$VIRTUAL_ENV" ] && [ -z "$CONDA_DEFAULT_ENV" ]; then
    echo "创建虚拟环境..."
    python3 -m venv .venv
    source .venv/bin/activate
fi

echo "安装依赖..."
pip install -q --upgrade pip
pip install -q -e .

echo ""
echo "✅ 依赖安装完成"
echo ""
echo "IDE解释器路径: $(which python)"
echo ""
echo "请在IDE中设置此路径作为Python解释器"

# 厂商数据库更新脚本

## 概述

`update_vendor_db.py` 脚本用于从 IEEE OUI 数据库自动获取 MAC 地址前缀（OUI）与厂商的对应关系，并更新厂商 JSON 数据库文件。

## 使用方法

### 基本用法（自动下载）

```bash
cd backend
python scripts/update_vendor_db.py
```

或者直接运行：

```bash
python backend/scripts/update_vendor_db.py
```

### 使用本地文件（如果下载失败）

如果遇到 HTTP 418 或其他网络错误，可以手动下载 OUI 数据库：

1. 从浏览器访问并下载：https://standards-oui.ieee.org/oui/oui.txt
2. 保存为 `oui.txt` 文件
3. 运行脚本时指定本地文件：

```bash
python scripts/update_vendor_db.py --local oui.txt
```

### 安装 requests 库（推荐）

如果遇到 HTTP 418 错误，脚本会自动尝试使用 `requests` 库。如果未安装，可以：

```bash
pip install requests
```

然后重新运行脚本。

### 功能说明

1. **从 IEEE OUI 数据库获取数据**
   - 脚本会从 IEEE 官方 OUI 数据库下载最新的 MAC 地址前缀与厂商对应关系
   - URL: https://standards-oui.ieee.org/oui/oui.txt

2. **自动更新厂商文件**
   - 脚本会识别以下厂商并更新对应的 JSON 文件：
     - Apple, Samsung, Xiaomi, Huawei, TP-Link, D-Link
     - Cisco, Lenovo, Dell, HP, Netgear, ASUS
     - Honor, OPPO, Vivo, OnePlus, LG, Redmi, Meizu

3. **保留现有数据**
   - 如果厂商文件已存在，脚本会合并新数据与现有数据
   - 不会覆盖已有的设备型号映射

## 输出

脚本会在 `backend/app/data/vendors/` 目录下更新或创建厂商 JSON 文件。

每个文件格式：
```json
{
  "vendor": "厂商名称",
  "description": "描述信息",
  "models": {
    "XX:XX:XX": ["设备型号1", "设备型号2", ...]
  }
}
```

## 注意事项

1. **网络连接**：脚本需要访问互联网下载 IEEE OUI 数据库
2. **执行时间**：首次运行可能需要几分钟时间下载和解析数据
3. **数据准确性**：IEEE OUI 数据库是官方数据源，但可能不包含所有设备型号的详细信息
4. **手动补充**：对于设备型号信息，可能需要手动补充到 JSON 文件中

## 故障排除

### HTTP 418 错误

如果遇到 HTTP 418 错误（服务器拒绝自动化请求），有以下解决方案：

1. **使用 requests 库**（推荐）：
   ```bash
   pip install requests
   python scripts/update_vendor_db.py
   ```
   脚本会自动尝试使用 requests 库作为备选方案。

2. **手动下载并使用本地文件**：
   - 从浏览器访问：https://standards-oui.ieee.org/oui/oui.txt
   - 保存为 `oui.txt`
   - 运行：`python scripts/update_vendor_db.py --local oui.txt`

### 其他问题

如果脚本运行失败：
1. 检查网络连接
2. 确认 Python 版本 >= 3.7
3. 检查 `backend/app/data/vendors/` 目录的写入权限
4. 查看错误日志了解详细错误信息

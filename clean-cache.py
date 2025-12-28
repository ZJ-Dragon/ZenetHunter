#!/usr/bin/env python3
"""
ZenetHunter 缓存清理工具

一键清除项目生成的所有缓存，确保代码更改后能正确运行。

用法:
    python clean-cache.py              # 清理所有缓存（不包括数据库和虚拟环境）
    python clean-cache.py --all        # 清理所有缓存（包括数据库和虚拟环境）
    python clean-cache.py --db         # 同时清理数据库文件
    python clean-cache.py --venv       # 同时清理虚拟环境
    python clean-cache.py --docker     # 同时清理 Docker 缓存
    python clean-cache.py --help       # 显示帮助信息
"""

import argparse
import os
import shutil
import sys
from pathlib import Path


# 颜色输出（跨平台）
class Colors:
    """ANSI 颜色代码"""
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    RESET = '\033[0m'
    
    @staticmethod
    def disable():
        """禁用颜色（Windows 或非终端）"""
        Colors.RED = ''
        Colors.GREEN = ''
        Colors.YELLOW = ''
        Colors.BLUE = ''
        Colors.MAGENTA = ''
        Colors.CYAN = ''
        Colors.WHITE = ''
        Colors.BOLD = ''
        Colors.RESET = ''


# 检测是否支持颜色
if sys.platform == 'win32':
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        # 启用 Windows 10+ ANSI 颜色支持
        kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
    except Exception:
        Colors.disable()
elif not sys.stdout.isatty():
    Colors.disable()


def print_colored(message: str, color: str = Colors.WHITE):
    """打印彩色消息"""
    print(f"{color}{message}{Colors.RESET}")


def remove_path(path: Path, description: str = None) -> bool:
    """
    删除路径（文件或目录）
    
    Args:
        path: 要删除的路径
        description: 描述信息（用于日志）
        
    Returns:
        是否成功删除
    """
    try:
        if path.exists():
            if path.is_file():
                path.unlink()
                print_colored(f"  ✓ 删除文件: {path}", Colors.GREEN)
            elif path.is_dir():
                shutil.rmtree(path)
                print_colored(f"  ✓ 删除目录: {path}", Colors.GREEN)
            return True
        return False
    except PermissionError:
        print_colored(f"  ✗ 权限不足: {path}", Colors.RED)
        return False
    except Exception as e:
        print_colored(f"  ✗ 删除失败 {path}: {e}", Colors.RED)
        return False


def find_and_remove_patterns(root: Path, patterns: list[str], description: str):
    """
    查找并删除匹配模式的文件/目录
    
    Args:
        root: 根目录
        patterns: 模式列表（支持通配符）
        description: 描述信息
    """
    found_any = False
    for pattern in patterns:
        for path in root.rglob(pattern):
            if remove_path(path):
                found_any = True
    
    if not found_any:
        print_colored(f"  - {description}: 未找到", Colors.YELLOW)
    return found_any


def clean_python_cache(root: Path) -> int:
    """清理 Python 缓存"""
    print_colored("\n[1/6] 清理 Python 缓存...", Colors.CYAN)
    count = 0
    
    # Python 缓存目录
    cache_dirs = [
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        ".coverage",
        "htmlcov",
        ".tox",
        ".nox",
    ]
    
    for cache_dir in cache_dirs:
        for path in root.rglob(cache_dir):
            if remove_path(path):
                count += 1
    
    # Python 缓存文件
    cache_files = [
        "*.pyc",
        "*.pyo",
        "*.pyd",
        "*.py[cod]",
        "*$py.class",
        ".coverage.*",
        "coverage.xml",
        "*.egg-info",
    ]
    
    for pattern in cache_files:
        for path in root.rglob(pattern):
            if remove_path(path):
                count += 1
    
    # 构建目录
    build_dirs = ["build", "dist", ".eggs", "develop-eggs", "downloads", "eggs", "parts", "sdist", "var", "wheels"]
    for build_dir in build_dirs:
        build_path = root / build_dir
        if remove_path(build_path):
            count += 1
    
    print_colored(f"  → 已清理 {count} 个 Python 缓存项", Colors.GREEN)
    return count


def clean_frontend_cache(root: Path) -> int:
    """清理前端缓存"""
    print_colored("\n[2/6] 清理前端缓存...", Colors.CYAN)
    count = 0
    
    frontend_dir = root / "frontend"
    if not frontend_dir.exists():
        print_colored("  - frontend 目录不存在，跳过", Colors.YELLOW)
        return 0
    
    # 前端缓存目录
    cache_dirs = [
        "dist",
        "build",
        ".vite",
        ".cache",
        ".parcel-cache",
        ".next",
        "out",
        ".nuxt",
        ".output",
        ".svelte-kit",
        "node_modules/.cache",
    ]
    
    for cache_dir in cache_dirs:
        cache_path = frontend_dir / cache_dir
        if remove_path(cache_path):
            count += 1
    
    # 前端缓存文件
    cache_files = [
        "*.tsbuildinfo",
        ".eslintcache",
        ".stylelintcache",
    ]
    
    for pattern in cache_files:
        for path in frontend_dir.rglob(pattern):
            if remove_path(path):
                count += 1
    
    print_colored(f"  → 已清理 {count} 个前端缓存项", Colors.GREEN)
    return count


def clean_logs(root: Path) -> int:
    """清理日志文件"""
    print_colored("\n[3/6] 清理日志文件...", Colors.CYAN)
    count = 0
    
    log_patterns = [
        "*.log",
        "*.log.*",
        "npm-debug.log*",
        "yarn-debug.log*",
        "yarn-error.log*",
        "lerna-debug.log*",
    ]
    
    for pattern in log_patterns:
        for path in root.rglob(pattern):
            # 跳过 node_modules 中的日志（太大）
            if "node_modules" not in str(path):
                if remove_path(path):
                    count += 1
    
    print_colored(f"  → 已清理 {count} 个日志文件", Colors.GREEN)
    return count


def clean_os_cache(root: Path) -> int:
    """清理操作系统缓存"""
    print_colored("\n[4/6] 清理操作系统缓存...", Colors.CYAN)
    count = 0
    
    # macOS
    macos_cache = [
        ".DS_Store",
        ".AppleDouble",
        ".LSOverride",
        "._*",
        ".Spotlight-V100",
        ".Trashes",
    ]
    
    # Windows
    windows_cache = [
        "Thumbs.db",
        "Thumbs.db:encryptable",
        "ehthumbs.db",
        "ehthumbs_vista.db",
        "Desktop.ini",
        "desktop.ini",
        "$RECYCLE.BIN",
        "*.lnk",
    ]
    
    # Linux
    linux_cache = [
        "*~",
        ".fuse_hidden*",
        ".directory",
        ".Trash-*",
        ".nfs*",
        "nohup.out",
    ]
    
    all_cache = macos_cache + windows_cache + linux_cache
    
    for pattern in all_cache:
        for path in root.rglob(pattern):
            if remove_path(path):
                count += 1
    
    print_colored(f"  → 已清理 {count} 个操作系统缓存项", Colors.GREEN)
    return count


def clean_ide_cache(root: Path) -> int:
    """清理 IDE 缓存"""
    print_colored("\n[5/6] 清理 IDE 缓存...", Colors.CYAN)
    count = 0
    
    # IDE 缓存目录
    ide_dirs = [
        ".idea",
        ".vscode",
        ".vs",
        "*.iml",
    ]
    
    for ide_dir in ide_dirs:
        if ide_dir.endswith("*.iml"):
            # 处理文件模式
            for path in root.rglob("*.iml"):
                if remove_path(path):
                    count += 1
        else:
            ide_path = root / ide_dir
            if remove_path(ide_path):
                count += 1
    
    # 编辑器交换文件
    swap_files = ["*.swp", "*.swo", "*.swn"]
    for pattern in swap_files:
        for path in root.rglob(pattern):
            if remove_path(path):
                count += 1
    
    print_colored(f"  → 已清理 {count} 个 IDE 缓存项", Colors.GREEN)
    return count


def clean_database(root: Path) -> int:
    """清理数据库文件"""
    print_colored("\n[6/6] 清理数据库文件...", Colors.CYAN)
    count = 0
    
    db_patterns = [
        "*.db",
        "*.sqlite",
        "*.sqlite3",
    ]
    
    for pattern in db_patterns:
        for path in root.rglob(pattern):
            # 只清理项目目录下的数据库，不清理系统数据库
            if "node_modules" not in str(path):
                if remove_path(path):
                    count += 1
    
    print_colored(f"  → 已清理 {count} 个数据库文件", Colors.GREEN)
    return count


def clean_venv(root: Path) -> int:
    """清理虚拟环境"""
    print_colored("\n[额外] 清理虚拟环境...", Colors.CYAN)
    count = 0
    
    venv_dirs = [
        ".venv",
        "venv",
        "ENV",
        "env",
        "venv.bak",
        "env.bak",
    ]
    
    for venv_dir in venv_dirs:
        venv_path = root / venv_dir
        if remove_path(venv_path):
            count += 1
        # 也检查子目录（如 backend/.venv）
        for path in root.rglob(venv_dir):
            if path.is_dir() and path != root:
                if remove_path(path):
                    count += 1
    
    print_colored(f"  → 已清理 {count} 个虚拟环境", Colors.GREEN)
    return count


def clean_docker_cache() -> int:
    """清理 Docker 缓存（需要用户确认）"""
    print_colored("\n[额外] 清理 Docker 缓存...", Colors.CYAN)
    
    try:
        import subprocess
        
        # 检查 Docker 是否可用
        result = subprocess.run(
            ["docker", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode != 0:
            print_colored("  - Docker 不可用，跳过", Colors.YELLOW)
            return 0
        
        print_colored("  ⚠  Docker 缓存清理需要确认，请手动运行:", Colors.YELLOW)
        print_colored("     docker system prune -a --volumes", Colors.CYAN)
        print_colored("  ⚠  或者清理特定项目:", Colors.YELLOW)
        print_colored("     docker compose down -v", Colors.CYAN)
        print_colored("     docker rmi zenethunter/*", Colors.CYAN)
        
        return 0
    except FileNotFoundError:
        print_colored("  - Docker 未安装，跳过", Colors.YELLOW)
        return 0
    except Exception as e:
        print_colored(f"  ✗ 检查 Docker 失败: {e}", Colors.RED)
        return 0


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="ZenetHunter 缓存清理工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python clean-cache.py              # 清理所有缓存（不包括数据库和虚拟环境）
  python clean-cache.py --all        # 清理所有缓存（包括数据库和虚拟环境）
  python clean-cache.py --db         # 同时清理数据库文件
  python clean-cache.py --venv       # 同时清理虚拟环境
  python clean-cache.py --docker     # 显示 Docker 清理建议
        """
    )
    
    parser.add_argument(
        "--all",
        action="store_true",
        help="清理所有缓存（包括数据库和虚拟环境）"
    )
    parser.add_argument(
        "--db",
        action="store_true",
        help="同时清理数据库文件"
    )
    parser.add_argument(
        "--venv",
        action="store_true",
        help="同时清理虚拟环境"
    )
    parser.add_argument(
        "--docker",
        action="store_true",
        help="显示 Docker 清理建议"
    )
    parser.add_argument(
        "--root",
        type=str,
        default=".",
        help="项目根目录（默认: 当前目录）"
    )
    
    args = parser.parse_args()
    
    # 获取项目根目录
    root = Path(args.root).resolve()
    
    if not root.exists():
        print_colored(f"错误: 目录不存在: {root}", Colors.RED)
        sys.exit(1)
    
    print_colored("=" * 60, Colors.BOLD)
    print_colored("ZenetHunter 缓存清理工具", Colors.BOLD + Colors.CYAN)
    print_colored("=" * 60, Colors.BOLD)
    print_colored(f"项目目录: {root}", Colors.WHITE)
    
    # 确认
    if args.all or args.db or args.venv:
        print_colored("\n⚠  警告: 将清理数据库/虚拟环境，这可能会删除重要数据！", Colors.YELLOW)
        response = input("是否继续? (yes/no): ").strip().lower()
        if response not in ["yes", "y"]:
            print_colored("已取消", Colors.YELLOW)
            sys.exit(0)
    
    total_count = 0
    
    # 执行清理
    total_count += clean_python_cache(root)
    total_count += clean_frontend_cache(root)
    total_count += clean_logs(root)
    total_count += clean_os_cache(root)
    total_count += clean_ide_cache(root)
    
    # 可选清理
    if args.all or args.db:
        total_count += clean_database(root)
    
    if args.all or args.venv:
        total_count += clean_venv(root)
    
    if args.all or args.docker:
        clean_docker_cache()
    
    # 总结
    print_colored("\n" + "=" * 60, Colors.BOLD)
    print_colored(f"清理完成！共清理 {total_count} 个项目", Colors.BOLD + Colors.GREEN)
    print_colored("=" * 60, Colors.BOLD)
    print_colored("\n提示: 下次运行前请重新安装依赖:", Colors.CYAN)
    print_colored("  - 后端: cd backend && pip install -e .", Colors.WHITE)
    print_colored("  - 前端: cd frontend && npm install", Colors.WHITE)


if __name__ == "__main__":
    main()

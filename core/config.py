#!/usr/bin/env python3
"""
配置管理模块
"""
import os
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent

# 目录配置
URLS_DIR = PROJECT_ROOT / 'urls'
TOOLS_DIR = PROJECT_ROOT / 'tools'
NIKTO_TOOLS_DIR = TOOLS_DIR / 'nikto'

# 超时配置（秒）
TIMEOUT_HTTPX = 120  # 增加到 2 分钟，避免超时
TIMEOUT_URL_COLLECTOR = 600  # 10分钟
TIMEOUT_URL_ANALYZER = 120   # 2分钟
TIMEOUT_NUCLEI = 900         # 15分钟
TIMEOUT_JS_ANALYZER = 300    # 5分钟
TIMEOUT_SQLMAP = 1200        # 20分钟

# 工具路径
def get_tool_path(tool_name):
    """获取工具路径"""
    if tool_name == 'url_collector':
        return NIKTO_TOOLS_DIR / 'katana_all_url.py'
    elif tool_name == 'url_analyzer':
        return NIKTO_TOOLS_DIR / 'url_analyzer.py'
    elif tool_name == 'nuclei_scanner':
        return NIKTO_TOOLS_DIR / 'scan.py'
    elif tool_name == 'js_analyzer':
        return NIKTO_TOOLS_DIR / 'js_analyzer.py'
    elif tool_name == 'sqlmap_scanner':
        return NIKTO_TOOLS_DIR / 'sqlmap_scan.py'
    else:
        raise ValueError(f"Unknown tool: {tool_name}")

# httpx 路径查找
def find_httpx():
    """查找 httpx 可执行文件"""
    import shutil
    
    httpx_exe = shutil.which('httpx-toolkit') or shutil.which('httpx') or 'httpx'
    
    # 如果找到的是 Python 的 httpx，尝试直接使用 Go bin 路径
    if 'python' in httpx_exe.lower() or 'scripts' in httpx_exe.lower():
        go_bin_paths = [
            Path.home() / 'go' / 'bin' / 'httpx.exe',
            Path.home() / '.local' / 'bin' / 'httpx',
            Path('/usr/local/bin/httpx'),
        ]
        for path in go_bin_paths:
            if path.exists():
                return str(path)
    
    return httpx_exe

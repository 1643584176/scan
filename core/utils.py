#!/usr/bin/env python3
"""
通用工具函数
"""
import sys
import io
import os
from datetime import datetime
from urllib.parse import urlparse

def setup_encoding():
    """设置 UTF-8 编码（Windows）"""
    if sys.platform == 'win32':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
        os.environ['PYTHONIOENCODING'] = 'utf-8'
        os.environ['PYTHONUTF8'] = '1'
        try:
            import ctypes
            ctypes.windll.kernel32.SetConsoleOutputCP(65001)
        except:
            pass

def log(message):
    """输出带时间戳的日志"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}] {message}", flush=True)

def get_domain(url):
    """从 URL 提取域名"""
    parsed = urlparse(url)
    return parsed.netloc

def get_bounty_dir(domain, base_dir='.'):
    """获取 bounty 目录路径"""
    return os.path.join(base_dir, f"@{domain}_bounty")

def ensure_dir(directory):
    """确保目录存在"""
    os.makedirs(directory, exist_ok=True)

def load_env_file(env_path):
    """加载 .env 文件"""
    if not os.path.exists(env_path):
        return False
    
    try:
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    if key not in os.environ:
                        os.environ[key] = value
        return True
    except Exception as e:
        print(f"[WARN] 加载 .env 文件失败: {e}")
        return False

def read_urls_from_file(file_path):
    """从文件读取 URL 列表"""
    if not os.path.exists(file_path):
        return []
    
    with open(file_path, 'r', encoding='utf-8') as f:
        urls = [line.strip() for line in f if line.strip() and not line.strip().startswith('#')]
    
    return urls

def write_urls_to_file(file_path, urls):
    """写入 URL 列表到文件"""
    with open(file_path, 'w', encoding='utf-8') as f:
        for url in urls:
            f.write(f"{url}\n")

#!/usr/bin/env python3
"""
URL 收集模块 - 调用 katana_all_url.py (Katana 爬虫)
可以单独运行: python modules/url_collector.py <url> <output_dir>
"""
import sys
import os
import subprocess

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.config import get_tool_path, TIMEOUT_URL_COLLECTOR
from core.utils import log, ensure_dir, read_urls_from_file, get_domain, get_bounty_dir

def collect_urls(url, output_dir='.'):
    """
    收集目标网站的所有 URL
    
    Args:
        url: 目标 URL
        output_dir: 输出目录
    
    Returns:
        list: URL 列表
    """
    ensure_dir(output_dir)
    
    all_urls_file = os.path.join(output_dir, 'all_urls.txt')
    
    # 检查是否已有 all_urls.txt
    if os.path.exists(all_urls_file):
        existing_urls = read_urls_from_file(all_urls_file)
        if existing_urls:
            log(f"发现已有的 all_urls.txt ({len(existing_urls)} 个 URL)，跳过爬取")
            return existing_urls
    
    log(f"开始 URL 收集: {url}")
    log("这个过程可能需要3-10分钟，请耐心等待...")
    
    try:
        tool_path = get_tool_path('url_collector')
        
        result = subprocess.run([
            sys.executable,
            str(tool_path),
            url,
            os.path.abspath(output_dir)
        ], cwd=os.getcwd(), timeout=TIMEOUT_URL_COLLECTOR)
        
        if result.returncode == 0:
            log("[✓] URL 收集完成")
        else:
            log(f"[!] URL 收集返回码 {result.returncode}")
        
        # 读取结果
        if os.path.exists(all_urls_file):
            urls = read_urls_from_file(all_urls_file)
            log(f"加载 {len(urls)} 个有效 URL")
            return urls
        else:
            log("未找到 all_urls.txt")
            return []
            
    except subprocess.TimeoutExpired:
        log("[✗] URL 收集超时（10分钟）")
        # 尝试使用已有的文件
        if os.path.exists(all_urls_file):
            urls = read_urls_from_file(all_urls_file)
            log(f"使用已有的 {len(urls)} 个 URL")
            return urls
        return []
    except Exception as e:
        log(f"[✗] URL 收集异常: {e}")
        return []

if __name__ == '__main__':
    # 如果提供了命令行参数，使用参数
    if len(sys.argv) >= 3:
        url = sys.argv[1]
        output_dir = sys.argv[2]
    else:
        # 否则从配置文件读取
        urls_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'urls', 'first_target.txt')
        urls = read_urls_from_file(urls_file)
        
        if not urls:
            print("错误: 未在 urls/first_target.txt 中找到 URL")
            sys.exit(1)
        
        url = urls[0]
        domain = get_domain(url)
        output_dir = get_bounty_dir(domain)
        
        # 确保输出目录存在
        ensure_dir(output_dir)
        print(f"从配置文件读取 URL: {url}")
        print(f"输出目录: {output_dir}\n")
    
    urls = collect_urls(url, output_dir)
    print(f"\n收集到 {len(urls)} 个 URL")

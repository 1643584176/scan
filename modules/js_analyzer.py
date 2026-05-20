#!/usr/bin/env python3
"""
JavaScript 文件分析模块
可以单独运行: python modules/js_analyzer.py <urls_file> <output_dir>
"""
import sys
import os
import subprocess

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.config import get_tool_path, TIMEOUT_JS_ANALYZER
from core.utils import log

def analyze_js_files(urls_file, output_dir='.'):
    """
    分析 JavaScript 文件
    
    Args:
        urls_file: URL 文件路径
        output_dir: 输出目录
    
    Returns:
        bool: 是否成功
    """
    if not os.path.exists(urls_file):
        log(f"URL 文件不存在: {urls_file}")
        return False
    
    log(f"开始 JavaScript 文件分析")
    
    try:
        tool_path = get_tool_path('js_analyzer')
        
        result = subprocess.run([
            sys.executable,
            str(tool_path),
            os.path.abspath(urls_file),
            os.path.abspath(output_dir)
        ], cwd=os.getcwd(), timeout=TIMEOUT_JS_ANALYZER)
        
        if result.returncode == 0:
            log("[✓] JavaScript 分析完成")
            return True
        else:
            log(f"[!] JavaScript 分析返回码 {result.returncode}")
            return False
            
    except Exception as e:
        log(f"[✗] JavaScript 分析异常: {e}")
        return False

if __name__ == '__main__':
    # 如果提供了命令行参数，使用参数
    if len(sys.argv) >= 3:
        urls_file = sys.argv[1]
        output_dir = sys.argv[2]
    else:
        # 否则从默认位置读取
        from core.utils import get_domain, get_bounty_dir, read_urls_from_file
        
        # 先读取目标 URL 确定输出目录
        target_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'urls', 'first_target.txt')
        targets = read_urls_from_file(target_file)
        
        if not targets:
            print("错误: 未在 urls/first_target.txt 中找到 URL")
            sys.exit(1)
        
        domain = get_domain(targets[0])
        output_dir = get_bounty_dir(domain)
        
        # 默认的 all_urls.txt 路径
        urls_file = os.path.join(output_dir, 'all_urls.txt')
        
        if not os.path.exists(urls_file):
            print(f"错误: 找不到 {urls_file}")
            print("请先运行 url_collector.py")
            sys.exit(1)
        
        print(f"使用 URL 文件: {urls_file}")
        print(f"输出目录: {output_dir}\n")
    
    success = analyze_js_files(urls_file, output_dir)
    sys.exit(0 if success else 1)

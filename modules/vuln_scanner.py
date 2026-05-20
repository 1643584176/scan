#!/usr/bin/env python3
"""
Nuclei 漏洞扫描模块
可以单独运行: python modules/vuln_scanner.py <url> <output_dir>
"""
import sys
import os
import subprocess

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.config import get_tool_path, TIMEOUT_NUCLEI
from core.utils import log, read_urls_from_file

def scan_vulnerabilities(url, output_dir='.'):
    """
    使用 Nuclei 进行漏洞扫描
    
    Args:
        url: 目标 URL
        output_dir: 输出目录
    
    Returns:
        list: 发现的漏洞列表
    """
    log(f"开始 Nuclei 漏洞扫描: {url}")
    log("Nuclei 扫描需要3-5分钟，请耐心等待...")
    
    try:
        tool_path = get_tool_path('nuclei_scanner')
        
        # 从环境变量读取扫描模式，默认为 standard
        scan_mode = os.environ.get('NUCLEI_MODE', 'standard')
        log(f"Nuclei 扫描模式: {scan_mode}")
        
        # 直接显示实时输出
        result = subprocess.run([
            sys.executable,
            str(tool_path),
            url,
            os.path.abspath(output_dir),
            scan_mode  # 传递扫描模式
        ], cwd=os.getcwd(), timeout=TIMEOUT_NUCLEI)
        
        if result.returncode == 0:
            log("[✓] Nuclei 扫描完成")
        else:
            log(f"[!] Nuclei 扫描返回码 {result.returncode}")
        
        # 读取扫描结果
        nuclei_file = os.path.join(output_dir, 'nuclei_scan.txt')
        if os.path.exists(nuclei_file):
            with open(nuclei_file, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = [line.strip() for line in content.splitlines() if line.strip()]
                log(f"发现 {len(lines)} 个结果")
                return lines
        else:
            log("未找到扫描结果文件")
            return []
            
    except subprocess.TimeoutExpired:
        log("[✗] Nuclei 扫描超时（15分钟）")
        return []
    except Exception as e:
        log(f"[✗] Nuclei 扫描异常: {e}")
        return []

if __name__ == '__main__':
    # 如果提供了命令行参数，使用参数
    if len(sys.argv) >= 3:
        url = sys.argv[1]
        output_dir = sys.argv[2]
    else:
        # 否则从配置文件读取
        from core.utils import get_domain, get_bounty_dir, read_urls_from_file
        
        target_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'urls', 'first_target.txt')
        targets = read_urls_from_file(target_file)
        
        if not targets:
            print("错误: 未在 urls/first_target.txt 中找到 URL")
            sys.exit(1)
        
        url = targets[0]
        domain = get_domain(url)
        output_dir = get_bounty_dir(domain)
        
        print(f"从配置文件读取 URL: {url}")
        print(f"输出目录: {output_dir}\n")
    
    vulnerabilities = scan_vulnerabilities(url, output_dir)
    print(f"\n发现 {len(vulnerabilities)} 个漏洞/结果")

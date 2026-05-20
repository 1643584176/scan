#!/usr/bin/env python3
"""
技术栈检测模块 - 使用 httpx
可以单独运行: python modules/tech_detect.py <url> <output_dir>
"""
import sys
import os
import subprocess
import json

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.config import find_httpx, TIMEOUT_HTTPX
from core.utils import log, ensure_dir

def detect_tech_stack(url, output_dir='.'):
    """
    使用 httpx 检测技术栈
    
    Args:
        url: 目标 URL
        output_dir: 输出目录
    
    Returns:
        dict: 包含 tech_stack 和 tech_details
    """
    ensure_dir(output_dir)
    
    log(f"开始 HTTP 探测: {url}")
    
    try:
        httpx_exe = find_httpx()
        
        log(f"使用 httpx: {httpx_exe}")
        
        # 输出到临时文件，避免 capture_output 阻塞
        temp_output = os.path.join(output_dir, 'temp_tech_detect.txt')
        
        result = subprocess.run([
            httpx_exe,
            '-u', url,
            '-o', temp_output,  # 输出到文件
            '-timeout', '30',   # 单个请求超时 30 秒
            '-retries', '2',    # 重试 2 次
            '-silent',
            '-sc', '-title', '-tech-detect'
        ], timeout=TIMEOUT_HTTPX)
        
        if result.returncode == 0 and os.path.exists(temp_output):
            log("[✓] HTTP 探测完成")
            
            # 从文件读取输出
            with open(temp_output, 'r', encoding='utf-8') as f:
                stdout_text = f.read()
            
            # 解析技术栈信息
            tech_stack = []
            tech_details = {}
            
            for line in stdout_text.splitlines():
                if line.strip():
                    parts = line.split()
                    if len(parts) > 2:
                        tech_stack.append('HTTP')
                        # 可以进一步解析技术细节
            
            # 保存结果
            output_file = os.path.join(output_dir, 'tech_stack.json')
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'url': url,
                    'tech_stack': tech_stack,
                    'tech_details': tech_details,
                    'raw_output': stdout_text
                }, f, indent=2, ensure_ascii=False)
            
            # 清理临时文件
            if os.path.exists(temp_output):
                os.remove(temp_output)
            
            log(f"技术栈结果已保存到: {output_file}")
            return {
                'tech_stack': tech_stack,
                'tech_details': tech_details
            }
        else:
            log("[!] HTTP 探测返回非零退出码")
            return {'tech_stack': [], 'tech_details': {}}
            
    except subprocess.TimeoutExpired:
        log("[✗] HTTP 探测超时（120秒）")
        log("   [INFO] 可能原因:")
        log("   - 目标网站响应缓慢或有防护")
        log("   - 网络连接不稳定")
        log("   - 防火墙/WAF 拦截")
        log("   [TIP] 可以手动测试: httpx -u " + url)
        return {'tech_stack': [], 'tech_details': {}}
    except Exception as e:
        log(f"[✗] HTTP 探测异常: {e}")
        import traceback
        log(f"   [DEBUG] {traceback.format_exc()[:200]}")
        return {'tech_stack': [], 'tech_details': {}}

if __name__ == '__main__':
    import sys
    
    # 如果提供了命令行参数，使用参数
    if len(sys.argv) >= 3:
        url = sys.argv[1]
        output_dir = sys.argv[2]
    else:
        # 否则从配置文件读取
        from core.utils import read_urls_from_file, get_domain, get_bounty_dir
        
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
    
    result = detect_tech_stack(url, output_dir)
    print(f"\n检测到的技术栈: {result['tech_stack']}")

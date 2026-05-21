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
    使用 httpx 和多种方法检测技术栈（增强版）
    
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
            '-sc', '-title', '-tech-detect', '-server', '-ip'
        ], timeout=TIMEOUT_HTTPX)
        
        if result.returncode == 0 and os.path.exists(temp_output):
            log("[✓] HTTP 探测完成")
            
            # 从文件读取输出
            with open(temp_output, 'r', encoding='utf-8') as f:
                stdout_text = f.read()
            
            # 解析技术栈信息（增强版）
            tech_stack = []
            tech_details = {}
            
            for line in stdout_text.splitlines():
                if not line.strip():
                    continue
                
                # httpx 输出格式: [STATUS] [URL] [TITLE] [TECH]
                parts = line.split()
                if len(parts) < 2:
                    continue
                
                # 提取状态码
                try:
                    status_code = parts[0].strip('[]')
                    tech_details['status_code'] = status_code
                except:
                    pass
                
                # 提取技术栈（通常在最后一部分）
                tech_part = parts[-1] if len(parts) > 1 else ''
                
                # 解析常见的技术标识
                tech_keywords = {
                    'React': ['react', 'next.js'],
                    'Vue': ['vue', 'nuxt'],
                    'Angular': ['angular'],
                    'jQuery': ['jquery'],
                    'Bootstrap': ['bootstrap'],
                    'WordPress': ['wordpress', 'wp'],
                    'Nginx': ['nginx'],
                    'Apache': ['apache'],
                    'Cloudflare': ['cloudflare'],
                    'AWS': ['amazon', 'aws', 'elb'],
                    'Express': ['express'],
                    'Django': ['django'],
                    'Flask': ['flask'],
                    'Spring': ['spring'],
                    'Laravel': ['laravel'],
                    'Ruby on Rails': ['rails', 'rack'],
                    'PHP': ['php'],
                    'Node.js': ['node'],
                    'IIS': ['iis', 'microsoft-iis'],
                }
                
                line_lower = line.lower()
                detected_techs = []
                
                for tech_name, keywords in tech_keywords.items():
                    if any(kw in line_lower for kw in keywords):
                        detected_techs.append(tech_name)
                        if tech_name not in tech_stack:
                            tech_stack.append(tech_name)
                
                if detected_techs:
                    tech_details['detected_technologies'] = detected_techs
                
                # 提取服务器信息
                if 'server:' in line_lower or 'x-powered-by:' in line_lower:
                    tech_details['server_info'] = line
            
            # 额外：尝试通过特征文件检测
            additional_techs = detect_via_fingerprinting(url)
            for tech in additional_techs:
                if tech not in tech_stack:
                    tech_stack.append(tech)
            
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
            
            log(f"检测到的技术栈: {', '.join(tech_stack) if tech_stack else '未检测到具体技术'}")
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

def detect_via_fingerprinting(url):
    """
    通过特征文件检测技术栈
    
    Args:
        url: 目标 URL
    
    Returns:
        list: 检测到的技术列表
    """
    import requests
    detected = []
    
    # 定义常见技术的特征文件路径
    fingerprint_paths = {
        'WordPress': [
            '/wp-login.php',
            '/wp-content/',
            '/wp-includes/',
        ],
        'Drupal': [
            '/sites/',
            '/core/misc/drupal.js',
        ],
        'Joomla': [
            '/media/system/js/core.js',
            '/administrator/',
        ],
        'Magento': [
            '/static/frontend/',
            '/pub/static/',
        ],
        'Shopify': [
            '/cdn.shopify.com',
        ],
        'GitHub Pages': [
            '/cdn.cookielaw.org',
        ],
    }
    
    try:
        # 获取主页内容用于分析
        resp = requests.get(url, timeout=10, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
        })
        
        if resp.status_code == 200:
            content = resp.text.lower()
            headers = resp.headers
            
            # 检查 HTML 内容中的特征
            if 'wp-content' in content or 'wp-includes' in content:
                detected.append('WordPress')
            
            if 'drupal' in content:
                detected.append('Drupal')
            
            if 'joomla' in content:
                detected.append('Joomla')
            
            if 'magento' in content:
                detected.append('Magento')
            
            if 'shopify' in content or 'cdn.shopify.com' in content:
                detected.append('Shopify')
            
            # 检查响应头
            if 'x-powered-by' in headers:
                powered_by = headers['x-powered-by'].lower()
                if 'express' in powered_by:
                    detected.append('Express')
                elif 'asp.net' in powered_by:
                    detected.append('ASP.NET')
                elif 'php' in powered_by:
                    detected.append('PHP')
            
            if 'server' in headers:
                server = headers['server'].lower()
                if 'nginx' in server:
                    detected.append('Nginx')
                elif 'apache' in server:
                    detected.append('Apache')
                elif 'iis' in server:
                    detected.append('IIS')
            
            # 检查 meta 标签
            import re
            generator_match = re.search(r'<meta[^>]+name=["\']generator["\'][^>]+content=["\']([^"\']+)["\']', content)
            if generator_match:
                generator = generator_match.group(1).lower()
                if 'wordpress' in generator:
                    detected.append('WordPress')
                elif 'drupal' in generator:
                    detected.append('Drupal')
                elif 'joomla' in generator:
                    detected.append('Joomla')
    
    except Exception as e:
        log(f"[WARN] 指纹检测失败: {e}")
    
    return list(set(detected))  # 去重

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

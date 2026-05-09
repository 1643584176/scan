#!/usr/bin/env python3
"""
增强版技术栈检测（HTTP头 + HTML分析）。
用法: python scan_enhanced.py <目标URL>
"""

import httpx
from bs4 import BeautifulSoup
import json
import re
from datetime import datetime

def analyze_headers(url):
    """分析 HTTP 响应头识别技术"""
    techs = {}
    
    try:
        # 添加 headers 模拟浏览器，避免被屏蔽
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        }
        
        response = httpx.get(url, timeout=10, follow_redirects=True, headers=headers)
        response_headers = response.headers
        
        # Web 服务器
        server = response_headers.get('Server', '')
        if server:
            if 'nginx' in server.lower():
                techs['Nginx'] = ''
            elif 'apache' in server.lower():
                techs['Apache'] = ''
            elif 'iis' in server.lower():
                techs['Microsoft IIS'] = ''
            elif 'cloudflare' in server.lower():
                techs['Cloudflare'] = ''
        
        # X-Powered-By
        powered_by = response_headers.get('X-Powered-By', '')
        if powered_by:
            if 'express' in powered_by.lower():
                techs['Express'] = ''
            elif 'asp.net' in powered_by.lower():
                techs['ASP.NET'] = ''
            elif 'php' in powered_by.lower():
                techs['PHP'] = ''
        
        # CDN 检测
        cdn_headers = ['cf-ray', 'x-amz-cf-id', 'x-cache']
        for header in cdn_headers:
            if header in response_headers:
                if 'cf-ray' in header:
                    techs['Cloudflare CDN'] = ''
                elif 'amz-cf' in header:
                    techs['Amazon CloudFront'] = ''
                break
        
        # 缓存系统
        via = response_headers.get('Via', '')
        if 'varnish' in via.lower():
            techs['Varnish'] = ''
        
        return techs
        
    except Exception as e:
        print(f"HTTP 头分析错误: {e}")
        return {}

def analyze_html(url):
    """分析 HTML 内容识别技术"""
    techs = {}
    
    try:
        # 添加 headers 模拟浏览器
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        }
        
        response = httpx.get(url, timeout=10, follow_redirects=True, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 检测 JavaScript 库
        scripts = soup.find_all('script', src=True)
        for script in scripts:
            src = script['src'].lower()
            if 'jquery' in src:
                match = re.search(r'jquery[/-]([0-9.]+)', src)
                version = match.group(1) if match else ''
                techs['jQuery'] = version
            elif 'react' in src:
                techs['React'] = ''
            elif 'vue' in src:
                techs['Vue.js'] = ''
            elif 'angular' in src:
                techs['Angular'] = ''
            elif 'bootstrap' in src:
                match = re.search(r'bootstrap[/-]([0-9.]+)', src)
                version = match.group(1) if match else ''
                techs['Bootstrap'] = version
        
        # 检测 CSS 框架
        links = soup.find_all('link', rel='stylesheet')
        for link in links:
            href = link.get('href', '').lower()
            if 'bootstrap' in href and 'Bootstrap' not in techs:
                match = re.search(r'bootstrap[/-]([0-9.]+)', href)
                version = match.group(1) if match else ''
                techs['Bootstrap'] = version
            elif 'tailwind' in href:
                techs['Tailwind CSS'] = ''
            elif 'font-awesome' in href or 'fontawesome' in href:
                techs['Font Awesome'] = ''
        
        # 检测 Meta 生成器
        meta_generator = soup.find('meta', attrs={'name': 'generator'})
        if meta_generator:
            content = meta_generator.get('content', '')
            if 'wordpress' in content.lower():
                techs['WordPress'] = ''
            elif 'joomla' in content.lower():
                techs['Joomla'] = ''
            elif 'drupal' in content.lower():
                techs['Drupal'] = ''
        
        # 检测 HTML 注释中的信息
        comments = soup.find_all(string=lambda text: isinstance(text, str) and '<!--' in str(text))
        for comment in comments:
            comment_str = str(comment).lower()
            if 'wordpress' in comment_str and 'WordPress' not in techs:
                techs['WordPress'] = ''
        
        return techs
        
    except Exception as e:
        print(f"HTML 分析错误: {e}")
        return {}

def run_enhanced_scan(target):
    output_file = f"enhanced_scan_{target.replace('http://', '').replace('https://', '').replace('/', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    print("🔍 正在分析 HTTP 头和 HTML...")
    
    # 分析 HTTP 头
    header_techs = analyze_headers(target)
    
    # 分析 HTML
    html_techs = analyze_html(target)
    
    # 合并结果
    all_techs = {**header_techs, **html_techs}
    
    if all_techs:
        # 保存结果
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_techs, f, indent=4, ensure_ascii=False)
        
        print(f"增强检测数据已保存到 {output_file}")
        
        # 显示检测到的技术
        tech_list = [f"{name} v{ver}" if ver else name for name, ver in all_techs.items()]
        print(f"检测到的技术: {', '.join(tech_list)}")
        
        return list(all_techs.keys())
    else:
        print("未检测到额外技术")
        return []

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("用法: python scan_enhanced.py <目标URL>")
        sys.exit(1)
    target = sys.argv[1]
    run_enhanced_scan(target)

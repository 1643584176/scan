#!/usr/bin/env python3
"""
简单的HTTP头和技术检测工具
"""

import requests
from urllib.parse import urlparse

def detect_tech(url):
    """检测网站技术栈"""
    print(f"\n🔍 正在分析: {url}\n")
    
    try:
        # 发送请求
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10, allow_redirects=True)
        
        print("📊 HTTP响应信息:")
        print(f"   状态码: {response.status_code}")
        print(f"   Server: {response.headers.get('Server', '未知')}")
        print(f"   X-Powered-By: {response.headers.get('X-Powered-By', '未知')}")
        print(f"   Content-Type: {response.headers.get('Content-Type', '未知')}")
        
        # 检测常见框架
        tech_stack = []
        
        # 检查HTML内容
        html = response.text.lower()
        
        if 'wordpress' in html:
            tech_stack.append('WordPress')
        if 'react' in html or 'reactjs' in html:
            tech_stack.append('React')
        if 'vue' in html:
            tech_stack.append('Vue.js')
        if 'angular' in html:
            tech_stack.append('Angular')
        if 'jquery' in html:
            tech_stack.append('jQuery')
        if 'bootstrap' in html:
            tech_stack.append('Bootstrap')
        
        # 检查响应头
        server = response.headers.get('Server', '').lower()
        if 'nginx' in server:
            tech_stack.append('Nginx')
        elif 'apache' in server:
            tech_stack.append('Apache')
        elif 'cloudflare' in server:
            tech_stack.append('Cloudflare')
        
        powered_by = response.headers.get('X-Powered-By', '').lower()
        if 'express' in powered_by:
            tech_stack.append('Express.js')
        elif 'asp.net' in powered_by:
            tech_stack.append('ASP.NET')
        elif 'php' in powered_by:
            tech_stack.append('PHP')
        
        print(f"\n🎯 检测到的技术栈:")
        if tech_stack:
            for tech in tech_stack:
                print(f"   - {tech}")
        else:
            print("   未检测到明显的前端框架")
        
        # 保存结果
        domain = urlparse(url).netloc
        output_file = f"tech_detect_{domain.replace('.', '_')}.txt"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"目标: {url}\n")
            f.write(f"状态码: {response.status_code}\n")
            f.write(f"Server: {response.headers.get('Server', 'N/A')}\n")
            f.write(f"技术栈: {', '.join(tech_stack) if tech_stack else '未检测到'}\n")
            f.write(f"\n响应头:\n")
            for key, value in response.headers.items():
                f.write(f"{key}: {value}\n")
        
        print(f"\n✅ 结果已保存到: {output_file}")
        
        return tech_stack
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        return []


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        url = input("输入目标URL: ").strip()
    
    detect_tech(url)

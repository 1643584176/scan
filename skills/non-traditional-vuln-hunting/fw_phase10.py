# -*- coding: utf-8 -*-
"""Phase10: PG SSLRequest 特殊路径 + 无 SNI TLS + allowedCIDRs 新字段"""
import sys, time, socket
sys.path.insert(0, r'D:\scan\skills\non-traditional-vuln-hunting')
from fw_driver import api, cmd, TEAM, fresh_sandbox_deny_all

SID = fresh_sandbox_deny_all("fwtest4")

GUEST = r'''
import socket, struct, time

def tcp_conn(ip, port, timeout=6):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(timeout)
    s.connect((ip, port))
    return s

def pg_probe(ip, port):
    # PG SSLRequest: len=8 + 80877103
    req = struct.pack('>I', 8) + struct.pack('>I', 80877103)
    try:
        s = tcp_conn(ip, port)
        s.sendall(req)
        try:
            r = s.recv(1)
            print('[pg %s:%d] resp=%r' % (ip, port, r), flush=True)
        except socket.timeout:
            print('[pg %s:%d] recv TIMEOUT (no proxy answer)' % (ip, port), flush=True)
        s.close()
    except Exception as e:
        print('[pg %s:%d] EXC %s' % (ip, port, e), flush=True)

def tls_ch(hostname=None):
    # minimal TLS1.3 ClientHello, record-layer length correct (2 bytes)
    body = b'\x03\x03' + b'\x11' * 32  # version + random
    body += b'\x00'                    # session id len 0
    body += b'\x00\x02\x13\x01'        # cipher TLS_AES_128_GCM_SHA256
    body += b'\x01\x00'                # compression: null
    ext = b''
    if hostname:
        n = hostname.encode()
        sni = b'\x00' + bytes([len(n)]) + n
        ext += b'\x00\x00' + struct.pack('>H', len(sni)) + sni
    body += struct.pack('>H', len(ext)) + ext
    hs = b'\x01' + len(body).to_bytes(3, 'big') + body
    return b'\x16\x03\x01' + struct.pack('>H', len(hs)) + hs

def tls_probe(ip, port, hostname=None, label=''):
    try:
        s = tcp_conn(ip, port)
        s.sendall(tls_ch(hostname))
        s.settimeout(6)
        r = s.recv(200)
        print('[tls%s %s:%d] resp=%r' % (label, ip, port, r[:40]), flush=True)
        s.close()
    except Exception as e:
        print('[tls%s %s:%d] EXC %s' % (label, ip, port, e), flush=True)

# --- A: PG SSLRequest 特殊路径(custom 白名单=webhook.site) ---
# 非白名单 IP(应被连接层拦, 若回 S = 特殊路径)
pg_probe('34.195.135.204', 5432)
# 白名单 IP 任意端口
pg_probe('178.63.67.153', 5432)
# 白名单 IP 其他端口也试试 PG
pg_probe('178.63.67.153', 9999)

# --- B: 无 SNI TLS(custom 下白名单 IP) ---
tls_probe('178.63.67.153', 443, hostname=None, label='-noSNI')
# 带 SNI 对照
tls_probe('178.63.67.153', 443, hostname='webhook.site', label='-SNI')
print('done', flush=True)
'''

code = "cat > /tmp/pg18.py <<'PYEOF'\n" + GUEST + "\nPYEOF\npython3 /tmp/pg18.py"

GUEST2 = r'''
import socket
def tcp_probe(ip, port):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(5)
        s.connect((ip, port))
        print('[%s:%d] CONNECT OK' % (ip, port), flush=True)
        s.close()
    except Exception as e:
        print('[%s:%d] EXC %s' % (ip, port, e), flush=True)

tcp_probe('178.63.67.153', 80)
tcp_probe('178.63.67.154', 80)
print('done', flush=True)
'''
code2 = "cat > /tmp/pg18b.py <<'PYEOF'\n" + GUEST2 + "\nPYEOF\npython3 /tmp/pg18b.py"

if __name__ == "__main__":
    # 组A: custom 白名单 webhook.site
    body = {"mode": "custom", "allowedDomains": ["webhook.site"]}
    c, r = api("POST", "/v2/sandboxes/sessions/%s/network-policy?teamId=%s" % (SID, TEAM), body)
    print('set custom webhook.site:', c, r[:200], flush=True)
    time.sleep(2)
    c, r = cmd(SID, "bash", ["-lc", code], timeout_ms=90000)
    print('cmdA:', c, flush=True)
    print(r[:4000], flush=True)

    # 组B: allowedCIDRs 新字段(与 subnets 对比)
    body = {"mode": "custom", "allowedCIDRs": ["178.63.67.153/32"]}
    c, r = api("POST", "/v2/sandboxes/sessions/%s/network-policy?teamId=%s" % (SID, TEAM), body)
    print('set allowedCIDRs:', c, r[:300], flush=True)
    time.sleep(2)
    c, r = cmd(SID, "bash", ["-lc", code2], timeout_ms=60000)
    print('cmdB:', c, flush=True)
    print(r[:2000], flush=True)

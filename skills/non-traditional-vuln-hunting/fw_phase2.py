# -*- coding: utf-8 -*-
"""Phase2: deny-all 下本地面/内网/IPv6/metadata 探测"""
import sys
sys.path.insert(0, r'D:\scan\skills\non-traditional-vuln-hunting')
from fw_driver import cmd

SID = "sbx_6M8Yg7kJadsCnQ8GlDyTeZJa6VaY"

GUEST = r'''
import socket, struct, time, subprocess

def t(name, fn):
    try:
        r = fn()
        print('[%s] -> %r' % (name, r), flush=True)
    except Exception as e:
        print('[%s] EXC %s: %s' % (name, type(e).__name__, e), flush=True)

def tcp(ip, port, payload=b'', wait=3):
    s = socket.create_connection((ip, port), timeout=5)
    s.settimeout(wait)
    if payload:
        s.sendall(payload)
    try:
        return s.recv(4096)
    finally:
        s.close()

print('--- ifconfig ---', flush=True)
print(subprocess.run(['ip', 'addr'], capture_output=True, text=True).stdout[:1500], flush=True)
print(subprocess.run(['ip', 'route'], capture_output=True, text=True).stdout[:800], flush=True)

# 回环/本地面
t('lo 127.0.0.1:23456', lambda: tcp('127.0.0.1', 23456, b'ping\n'))
t('lo 127.0.0.1:30001', lambda: tcp('127.0.0.1', 30001, b'ping\n'))
t('lo 127.0.0.1:30002', lambda: tcp('127.0.0.1', 30002, b'ping\n'))
t('lo 127.0.0.1:8080', lambda: tcp('127.0.0.1', 8080, b'GET / HTTP/1.1\r\nHost: x\r\n\r\n'))

# metadata / 网关
t('169.254.169.254:80', lambda: tcp('169.254.169.254', 80, b'GET / HTTP/1.1\r\nHost: x\r\n\r\n'))
t('100.64.0.1:80', lambda: tcp('100.64.0.1', 80, b'GET / HTTP/1.1\r\nHost: x\r\n\r\n'))
t('100.64.0.1:443', lambda: tcp('100.64.0.1', 443, b''))
t('172.31.0.2:53', lambda: tcp('172.31.0.2', 53, b''))
t('172.31.0.2:80', lambda: tcp('172.31.0.2', 80, b'GET / HTTP/1.1\r\nHost: x\r\n\r\n'))

# IPv6
try:
    s = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
    s.settimeout(4)
    s.connect(('2606:4700:4700::1111', 443))
    print('[v6 1.1.1.1:443] CONNECTED', flush=True)
    s.close()
except Exception as e:
    print('[v6 1.1.1.1:443] EXC %s: %s' % (type(e).__name__, e), flush=True)

print('done', flush=True)
'''

code = "cat > /tmp/pg2.py <<'PYEOF'\n" + GUEST + "\nPYEOF\npython3 /tmp/pg2.py"

if __name__ == "__main__":
    c, r = cmd(SID, "bash", ["-lc", code], timeout_ms=90000)
    print("code:", c)
    print(r[:5000])

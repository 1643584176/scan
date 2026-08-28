# -*- coding: utf-8 -*-
"""Phase1: deny-all 下基线 + PG 特殊握手探测"""
import sys
sys.path.insert(0, r'D:\scan\skills\non-traditional-vuln-hunting')
from fw_driver import cmd

SID = "sbx_6M8Yg7kJadsCnQ8GlDyTeZJa6VaY"

GUEST = r'''
import socket, struct, time

IP = '178.63.67.153'

def t(name, fn):
    try:
        r = fn()
        print('[%s] -> %r' % (name, r), flush=True)
    except Exception as e:
        print('[%s] EXC %s: %s' % (name, type(e).__name__, e), flush=True)

def tcp(ip, port, payload=b'', wait=3):
    s = socket.create_connection((ip, port), timeout=6)
    s.settimeout(wait)
    if payload:
        s.sendall(payload)
    try:
        return s.recv(4096)
    finally:
        s.close()

def pg(ip, port):
    s = socket.create_connection((ip, port), timeout=6)
    s.settimeout(4)
    s.sendall(struct.pack('!II', 8, 0x04D2162F))
    try:
        return s.recv(4096)
    finally:
        s.close()

def udp(ip, port, payload, wait=3):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(wait)
    s.sendto(payload, (ip, port))
    try:
        return s.recv(4096)
    finally:
        s.close()

# 基线: deny-all 下 TCP
t('tcp80  GET /', lambda: tcp(IP, 80, b'GET / HTTP/1.1\r\nHost: webhook.site\r\nConnection: close\r\n\r\n'))
t('tcp443 conn', lambda: tcp(IP, 443))
# PG 握手探测
t('pg 443', lambda: pg(IP, 443))
t('pg 5432', lambda: pg(IP, 5432))
t('pg 80', lambda: pg(IP, 80))
# 对照: 知名 IP
t('pg 1.1.1.1:443', lambda: pg('1.1.1.1', 443))
# UDP 基线
t('udp 1.1.1.1:53', lambda: udp('1.1.1.1', 53, b'\x00\x01\x01\x00\x00\x01\x00\x00\x00\x00\x00\x00\x03www\x07example\x03com\x00\x00\x01\x00\x01'))
t('udp 8.8.8.8:53', lambda: udp('8.8.8.8', 53, b'\x00\x01\x01\x00\x00\x01\x00\x00\x00\x00\x00\x00\x03www\x07example\x03com\x00\x00\x01\x00\x01'))
t('udp webhook:123', lambda: udp(IP, 123, b'\x1b' + b'\x00' * 47))
print('done', flush=True)
'''

code = "cat > /tmp/pg1.py <<'PYEOF'\n" + GUEST + "\nPYEOF\npython3 /tmp/pg1.py"

if __name__ == "__main__":
    c, r = cmd(SID, "bash", ["-lc", code], timeout_ms=90000)
    print("code:", c)
    print(r[:4000])

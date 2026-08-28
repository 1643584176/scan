# -*- coding: utf-8 -*-
"""Phase3c: deny-all 下 DNS 面 - UDP 内网 DNS 是否放行 + DNS 隧道可行性"""
import sys
sys.path.insert(0, r'D:\scan\skills\non-traditional-vuln-hunting')
from fw_driver import api, cmd, TEAM

SID = "sbx_6M8Yg7kJadsCnQ8GlDyTeZJa6VaY"

GUEST = r'''
import socket, struct, time, subprocess

def t(name, fn):
    try:
        r = fn()
        print('[%s] -> %r' % (name, r), flush=True)
    except Exception as e:
        print('[%s] EXC %s: %s' % (name, type(e).__name__, e), flush=True)

def udp_send(ip, port, payload, wait=4):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(wait)
    s.sendto(payload, (ip, port))
    try:
        return s.recv(4096)
    finally:
        s.close()

def dns_query(ip, name):
    # 构造标准 DNS 查询 (A 记录)
    qid = 0x1234
    hdr = struct.pack('!HHHHHH', qid, 0x0100, 1, 0, 0, 0)
    qname = b''.join(bytes([len(x)]) + x.encode() for x in name.split('.')) + b'\x00'
    q = hdr + qname + struct.pack('!HH', 1, 1)
    return udp_send(ip, 53, q)

# 1. 内网 DNS UDP
t('udp 172.31.0.2:53', lambda: dns_query('172.31.0.2', 'webhook.site'))
# 2. 外网 DNS UDP
t('udp 1.1.1.1:53', lambda: dns_query('1.1.1.1', 'webhook.site'))
# 3. getaddrinfo 行为(deny-all 下系统解析是否可用)
try:
    r = socket.getaddrinfo('webhook.site', 80)
    print('[getaddrinfo webhook.site] -> %r' % (r[:1]), flush=True)
except Exception as e:
    print('[getaddrinfo] EXC %s: %s' % (type(e).__name__, e), flush=True)
# 4. curl 解析+连接(完整行为)
print(subprocess.run(['curl', '-s', '-m', '6', '-o', '/dev/null', '-w', '%{http_code} %{remote_ip}', 'http://webhook.site/57dad648-5daa-4ef8-8532-0d5dd3ceab68'], capture_output=True, text=True).stdout, flush=True)
# 5. 内网同段 TCP 抽查
for ip in ['100.64.75.134', '100.64.1.1', '100.64.2.1', '100.64.255.1']:
    t('tcp %s:23456' % ip, lambda ip=ip: socket.create_connection((ip, 23456), timeout=3))
print('done', flush=True)
'''

code = "cat > /tmp/pg5.py <<'PYEOF'\n" + GUEST + "\nPYEOF\npython3 /tmp/pg5.py"

if __name__ == "__main__":
    c, r = cmd(SID, "bash", ["-lc", code], timeout_ms=90000)
    print("code:", c)
    print(r[:5000])

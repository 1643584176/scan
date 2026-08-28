# -*- coding: utf-8 -*-
"""Phase5: custom 下 UDP 行为 + IP 直连/明文 HTTP 域名判断依据"""
import sys, time, struct
sys.path.insert(0, r'D:\scan\skills\non-traditional-vuln-hunting')
from fw_driver import api, cmd, TEAM

SID = "sbx_BQJ2aL59BOiIDLDpm6guM4rpiJih"

GUEST = r'''
import socket, struct, subprocess

def t(name, fn):
    try:
        r = fn()
        print('[%s] -> %r' % (name, r), flush=True)
    except Exception as e:
        print('[%s] EXC %s: %s' % (name, type(e).__name__, e), flush=True)

def udp(ip, port, payload, wait=4):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(wait)
    s.sendto(payload, (ip, port))
    try:
        return s.recv(4096)
    finally:
        s.close()

def dnsq(ip):
    hdr = struct.pack('!HHHHHH', 0x2222, 0x0100, 1, 0, 0, 0)
    qname = b'\x03www\x07example\x03com\x00'
    return udp(ip, 53, hdr + qname + struct.pack('!HH', 1, 1))

# UDP: 白名单域名 IP
t('udp webhook:123 NTP', lambda: udp('178.63.67.153', 123, b'\x1b' + b'\x00' * 47))
t('udp webhook:53 DNS', lambda: dnsq('178.63.67.153'))
t('udp webhook:9999', lambda: udp('178.63.67.153', 9999, b'HELLO' * 10))
# UDP: 非白名单外部
t('udp 1.1.1.1:53', lambda: dnsq('1.1.1.1'))
t('udp 8.8.8.8:53', lambda: dnsq('8.8.8.8'))
# UDP: 内网 DNS
t('udp 172.31.0.2:53', lambda: dnsq('172.31.0.2'))

# 明文 HTTP: IP 直连(无域名)
t('ip-direct :80', lambda: subprocess.run(['curl', '-s', '-m', '6', '-o', '/dev/null', '-w', '%{http_code} %{remote_ip}', 'http://178.63.67.153/'], capture_output=True, text=True).stdout)
# 明文 HTTP: Host 头=白名单域名, IP=白名单 IP
t('host-webhook ip-direct', lambda: subprocess.run(['curl', '-s', '-m', '6', '-o', '/dev/null', '-w', '%{http_code}', '-H', 'Host: webhook.site', 'http://178.63.67.153/'], capture_output=True, text=True).stdout)
# 明文 HTTP: Host 头=白名单域名, IP=非白名单(转发模型验证)
t('host-webhook ip-1111', lambda: subprocess.run(['curl', '-s', '-m', '6', '-o', '/dev/null', '-w', '%{http_code}', '--resolve', 'webhook.site:80:1.1.1.1', 'http://webhook.site/'], capture_output=True, text=True).stdout)
print('done', flush=True)
'''

code = "cat > /tmp/pg13.py <<'PYEOF'\n" + GUEST + "\nPYEOF\npython3 /tmp/pg13.py"

if __name__ == "__main__":
    body = {"mode": "custom", "allowedDomains": ["webhook.site"]}
    c, r = api("POST", "/v2/sandboxes/sessions/%s/network-policy?teamId=%s" % (SID, TEAM), body)
    print('set policy:', c, r[:200], flush=True)
    time.sleep(2)
    c, r = cmd(SID, "bash", ["-lc", code], timeout_ms=120000)
    print('cmd:', c, flush=True)
    print(r[:6000], flush=True)

# -*- coding: utf-8 -*-
"""Phase8: subnets.allow IP 白名单语义 - IP 直连/域名/DNS/端口面"""
import sys, time
sys.path.insert(0, r'D:\scan\skills\non-traditional-vuln-hunting')
from fw_driver import api, cmd, TEAM

SID = "sbx_BQJ2aL59BOiIDLDpm6guM4rpiJih"

GUEST = r'''
import socket, subprocess

def curl(args):
    r = subprocess.run(['curl', '-s', '-m', '6', '-k'] + args, capture_output=True, text=True)
    print('---', ' '.join(args)[:130], flush=True)
    print('RC=%d OUT:%s ERR:%s' % (r.returncode, r.stdout[:200].replace(chr(10),' '), r.stderr[:150].replace(chr(10),' ')), flush=True)

def tcp(ip, port, wait=3):
    s = socket.create_connection((ip, port), timeout=5)
    s.settimeout(wait)
    try:
        return s.recv(100)
    finally:
        s.close()

# IP 直连(白名单 IP)
curl(['http://178.63.67.153/'])
# IP 直连 443 (TLS, 无 SNI 域名匹配问题)
try:
    s = socket.create_connection(('178.63.67.153', 443), timeout=5)
    print('[tcp 178.63.67.153:443] CONNECTED', flush=True)
    s.close()
except Exception as e:
    print('[tcp 178.63.67.153:443] EXC %s' % e, flush=True)
# 任意端口(数据面端口检查)
try:
    s = socket.create_connection(('178.63.67.153', 2222), timeout=5)
    print('[tcp 178.63.67.153:2222] CONNECTED (port open!)', flush=True)
    s.close()
except Exception as e:
    print('[tcp 178.63.67.153:2222] EXC %s' % e, flush=True)
# 域名(解析结果在白名单)
curl(['https://webhook.site/'])
# 非白名单域名
curl(['https://httpbin.org/anything'])
# 非白名单 IP(负控)
curl(['http://1.1.1.1/'])
print('done', flush=True)
'''

code = "cat > /tmp/pg16.py <<'PYEOF'\n" + GUEST + "\nPYEOF\npython3 /tmp/pg16.py"

if __name__ == "__main__":
    body = {"subnets": {"allow": ["178.63.67.153/32"]}}
    c, r = api("POST", "/v2/sandboxes/sessions/%s/network-policy?teamId=%s" % (SID, TEAM), body)
    print('set subnets.allow:', c, r[:300], flush=True)
    time.sleep(2)
    c, r = cmd(SID, "bash", ["-lc", code], timeout_ms=90000)
    print('cmd:', c, flush=True)
    print(r[:5000], flush=True)

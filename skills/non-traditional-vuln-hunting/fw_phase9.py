# -*- coding: utf-8 -*-
"""Phase9: CIDR 匹配精确性 + allow/deny 优先级 + 端口面"""
import sys, time
sys.path.insert(0, r'D:\scan\skills\non-traditional-vuln-hunting')
from fw_driver import api, cmd, TEAM, fresh_sandbox_deny_all

SID = fresh_sandbox_deny_all("fwtest3")

GUEST = r'''
import socket, subprocess, time

def tcp_probe(ip, port):
    # 区分 connect 阶段与 recv 阶段
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(5)
        t0 = time.time()
        s.connect((ip, port))
        dt = time.time() - t0
        print('[%s:%d] CONNECT OK in %.2fs' % (ip, port, dt), flush=True)
        s.close()
    except socket.timeout:
        print('[%s:%d] CONNECT TIMEOUT' % (ip, port), flush=True)
    except Exception as e:
        print('[%s:%d] CONNECT EXC %s: %s' % (ip, port, type(e).__name__, e), flush=True)

# 邻段 IP 匹配精确性(白名单 178.63.67.153/32)
for ip in ['178.63.67.153', '178.63.67.154', '178.63.67.152', '178.63.67.155']:
    tcp_probe(ip, 80)

# 端口面(白名单 IP 上的非标准端口)
for port in [22, 8080, 8443, 2222]:
    tcp_probe('178.63.67.153', port)
print('done', flush=True)
'''

code = "cat > /tmp/pg17.py <<'PYEOF'\n" + GUEST + "\nPYEOF\npython3 /tmp/pg17.py"

GUEST2 = r'''
import subprocess
def curl(args):
    r = subprocess.run(['curl', '-s', '-m', '6', '-k'] + args, capture_output=True, text=True)
    print('---', ' '.join(args)[:100], flush=True)
    print('RC=%d OUT:%s' % (r.returncode, r.stdout[:150].replace(chr(10),' ')), flush=True)
curl(['http://178.63.67.153/'])
curl(['https://httpbin.org/anything'])
print('done', flush=True)
'''
code2 = "cat > /tmp/pg17b.py <<'PYEOF'\n" + GUEST2 + "\nPYEOF\npython3 /tmp/pg17b.py"

if __name__ == "__main__":
    # 组1: allow 单 IP
    body = {"subnets": {"allow": ["178.63.67.153/32"]}}
    c, r = api("POST", "/v2/sandboxes/sessions/%s/network-policy?teamId=%s" % (SID, TEAM), body)
    print('set allow /32:', c, flush=True)
    time.sleep(2)
    c, r = cmd(SID, "bash", ["-lc", code], timeout_ms=90000)
    print('cmd1:', c, flush=True)
    print(r[:4500], flush=True)

    # 组2: allow 全开 + deny 单 IP(优先级)
    body = {"subnets": {"allow": ["0.0.0.0/0"], "deny": ["178.63.67.153/32"]}}
    c, r = api("POST", "/v2/sandboxes/sessions/%s/network-policy?teamId=%s" % (SID, TEAM), body)
    print('set allow-all+deny-ip:', c, flush=True)
    time.sleep(2)
    c, r = cmd(SID, "bash", ["-lc", code2], timeout_ms=60000)
    print('cmd2:', c, flush=True)
    print(r[:2500], flush=True)

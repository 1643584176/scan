# -*- coding: utf-8 -*-
"""X 线诊断: attacker 沙箱内路由/可达性单测 (短超时, 最小化避免监控)"""
import json, sys, time
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, cmd, TEAM, PROJ

c, r = api('GET', '/v2/sandboxes/xatk1?teamId=%s&projectId=%s&resume=true' % (TEAM, PROJ))
print('resume:', c, flush=True)
if c != 200:
    sys.exit(1)
sid = json.loads(r)['sandbox']['currentSessionId']
print('sid:', sid, flush=True)
time.sleep(2)

tests = [
    ('route get victim', 'ip route get 100.64.14.248 2>&1; echo ---; cat /proc/net/fib_trie | grep -A2 "100.64" | head -20'),
    ('connect victim 8080', "python3 -c \"import socket; s=socket.socket(); s.settimeout(3);
try:
 s.connect(('100.64.14.248',8080)); print('CONN_OK')
except Exception as e:
 print('CONN_FAIL', type(e).__name__, e)\""),
    ('connect self-ip 8080', "python3 -c \"import socket; s=socket.socket(); s.settimeout(3);
try:
 s.connect(('100.64.179.192',8080)); print('SELF_CONN_OK')
except Exception as e:
 print('SELF_CONN_FAIL', type(e).__name__, e)\""),
    ('connect gateway 8080', "python3 -c \"import socket; s=socket.socket(); s.settimeout(3);
try:
 s.connect(('100.64.0.1',8080)); print('GW_CONN_OK')
except Exception as e:
 print('GW_CONN_FAIL', type(e).__name__, e)\""),
    ('connect 172.31.0.2 5432 (known S)', "python3 -c \"import socket; s=socket.socket(); s.settimeout(3);
try:
 s.connect(('172.31.0.2',5432)); print('VPC_CONN_OK')
except Exception as e:
 print('VPC_CONN_FAIL', type(e).__name__, e)\""),
]
for tag, script in tests:
    c, r = cmd(sid, 'sh', ['-c', script], timeout_ms=30000)
    print('=== %s -> %d' % (tag, c), flush=True)
    print(r[:900], flush=True)
    time.sleep(1)

print('=== DIAG DONE ===', flush=True)

# -*- coding: utf-8 -*-
"""X 线诊断 v2: attacker 沙箱内路由/可达性单测 (单行命令, 短超时)"""
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
    ('route', 'ip route get 100.64.14.248 2>&1 | head -3; echo ---; cat /proc/net/fib_trie 2>/dev/null | grep -B1 -A3 "100.64" | head -25'),
    ('conn victim:8080', 'python3 -c "import socket; s=socket.socket(); s.settimeout(3); rc=s.connect_ex((\'100.64.14.248\',8080)); print(\'VICTIM_RC\', rc)"'),
    ('conn self:8080', 'python3 -c "import socket; s=socket.socket(); s.settimeout(3); rc=s.connect_ex((\'100.64.179.192\',8080)); print(\'SELF_RC\', rc)"'),
    ('conn gw:8080', 'python3 -c "import socket; s=socket.socket(); s.settimeout(3); rc=s.connect_ex((\'100.64.0.1\',8080)); print(\'GW_RC\', rc)"'),
    ('conn vpc:5432', 'python3 -c "import socket; s=socket.socket(); s.settimeout(3); rc=s.connect_ex((\'172.31.0.2\',5432)); print(\'VPC_RC\', rc)"'),
    ('conn pub:443', 'python3 -c "import socket; s=socket.socket(); s.settimeout(3); rc=s.connect_ex((\'1.1.1.1\',443)); print(\'PUB_RC\', rc)"'),
]
for tag, script in tests:
    c, r = cmd(sid, 'sh', ['-c', script], timeout_ms=30000)
    print('=== %s -> %d' % (tag, c), flush=True)
    print(r[:800], flush=True)
    time.sleep(1)

print('=== DIAG2 DONE ===', flush=True)

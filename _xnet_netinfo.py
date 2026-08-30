# -*- coding: utf-8 -*-
"""X 线准备: 查看沙箱自身网络信息 (IP/网段/路由), 判断是否在 172.31.0.0/16"""
import base64, json, os, sys, time
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, cmd, TEAM, PROJ

# 1) 列出当前沙箱
c, r = api('GET', '/v2/sandboxes?teamId=%s&project=%s&limit=50' % (TEAM, PROJ))
print('list:', c, flush=True)
try:
    d = json.loads(r)
    for sb in d.get('sandboxes', []):
        print('  -', sb.get('name'), sb.get('id'), 'state=', sb.get('state'), 'sid=', sb.get('currentSessionId'), flush=True)
except Exception as e:
    print('parse err', e, r[:500], flush=True)

# 2) 创建新沙箱 (allow-all 便于排查; 稍后切 custom)
name = 'xnet1'
api('DELETE', '/v2/sandboxes/%s?teamId=%s&projectId=%s' % (name, TEAM, PROJ))
time.sleep(2)
body = {"projectId": PROJ, "name": name, "networkPolicy": {"mode": "custom", "allowedDomains": ["httpbin.org"]}}
c, r = api('POST', '/v2/sandboxes?teamId=%s' % TEAM, body)
print('create xnet1:', c, r[:300], flush=True)
if c != 200:
    sys.exit(1)
sid = json.loads(r)['sandbox']['currentSessionId']
print('sid:', sid, flush=True)
time.sleep(3)

# 3) 查看网络信息
cmds = [
    ('hostname -I', ['sh', '-c', 'hostname -I 2>/dev/null; ip -4 addr 2>/dev/null | grep -E "inet |eth|ens|enp"']),
    ('ip addr', ['ip', 'addr']),
    ('routes', ['ip', 'route']),
    ('dns', ['cat', '/etc/resolv.conf']),
    ('env proxy', ['env']),
]
for tag, cc in cmds:
    c, r = cmd(sid, cc[0], cc[1], timeout_ms=30000)
    print('=== %s -> %d' % (tag, c), flush=True)
    print(r[:1500], flush=True)
    time.sleep(1)

print('=== XNET1 NETINFO DONE ===', flush=True)

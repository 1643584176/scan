# -*- coding: utf-8 -*-
"""查 victim xvictim1 的 hit.log + 监听状态"""
import json, re, sys, urllib.request, urllib.error

raw = open(r'F:\scan\vercel_cookies2.txt', encoding='utf-8', errors='replace').read().strip()
m = re.search(r'authorization=\s*Bearer\s+(\S+)', raw, re.I)
TOK2 = m.group(1) if m else raw
TEAM2 = 'team_jnske5hDpDfj9eDG2PAfDqWf'
PROJ2 = 'prj_LX0QDsEAlWA0uRZvVTunSef3lllF'
BASE = 'https://api.vercel.com'

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

SID = 'sbx_kha5wxbV905yjutN6QyiONISv4d1'
# resume victim
c, r = api('GET', '/v2/sandboxes/xvictim1?teamId=%s&projectId=%s&resume=true' % (TEAM2, PROJ2))
print('resume victim:', c, flush=True)
if c == 200:
    SID = json.loads(r)['sandbox']['currentSessionId']
    print('sid:', SID, flush=True)

# 监听进程 + hit.log
c, r = cmd_v(SID, 'sh', ['-c', 'ps aux 2>/dev/null | grep -E "listen.py|python3" | grep -v grep; echo ---LOG---; cat /vercel/sandbox/hit.log 2>/dev/null; echo ---END---; ls -la /vercel/sandbox/'], timeout_ms=30000)
print('=== victim check ->', c, flush=True)
print(r[:3000], flush=True)

print('=== VICTIM POLL DONE ===', flush=True)

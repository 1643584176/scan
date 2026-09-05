# -*- coding: utf-8 -*-
"""v54c: runtime + persistent 组合面 — 行为差异/隔离边界
r1: runtime=python3.13 → guest 内 uid/权限对比
r2: persistent=true → 生命周期（delete 后 GET?）
r3: runtime 切换 → 数据保留？"""
import base64, json, sys, time, urllib.request, urllib.error
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, cmd, TOKEN, TEAM, PROJ

def api_raw(method, path, body=None, timeout=180, maxlen=400000):
    req = urllib.request.Request('https://api.vercel.com' + path, method=method)
    req.add_header('Authorization', 'Bearer ' + TOKEN)
    req.add_header('Content-Type', 'application/json')
    data = json.dumps(body).encode() if body is not None else None
    try:
        with urllib.request.urlopen(req, data=data, timeout=timeout) as r:
            return r.status, r.read().decode(errors='replace')[:maxlen]
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode(errors='replace')[:maxlen]
    except Exception as e:
        return -1, 'EXC %s' % str(e)[:120]

def parse_data(r):
    out = ''
    for line in r.splitlines():
        if '"data"' in line:
            try:
                out += json.loads(line).get('data', '')
            except Exception:
                pass
    return out

def run_cmd(sid, script, sudo=False):
    c, r = api_raw('POST', '/v2/sandboxes/sessions/%s/cmd?teamId=%s' % (sid, TEAM),
                   {"command": "bash", "args": ["-c", script], "wait": True, "logs": True,
                    "timeout": 30000, "sudo": sudo}, timeout=120)
    return c, parse_data(r)

if __name__ == '__main__':
    # ===== r1: runtime=python3.13 =====
    api_raw('DELETE', '/v2/sandboxes/rt53?teamId=%s&projectId=%s' % (TEAM, PROJ))
    time.sleep(2)
    c, r = api_raw('POST', '/v4/sandboxes?teamId=%s' % TEAM,
                   {"projectId": PROJ, "name": 'rt53', "runtime": 'python3.13'})
    print('[r1 create python3.13] -> %d %s' % (c, r[:200]), flush=True)
    if c == 200:
        sid = json.loads(r)['sandbox']['currentSessionId']
        time.sleep(8)
        c1, out1 = run_cmd(sid, "id; echo ---; ls /vercel; echo ---; cat /etc/os-release 2>/dev/null | head -3; echo ---; which python3 node 2>/dev/null; python3 --version 2>&1")
        print('[r1 python guest] -> %d' % c1, flush=True)
        print(out1.strip(), flush=True)
        api_raw('DELETE', '/v2/sandboxes/rt53?teamId=%s&projectId=%s' % (TEAM, PROJ))
    else:
        print('  runtime 参数被拒?', flush=True)

    time.sleep(3)
    # ===== r2: persistent=true =====
    api_raw('DELETE', '/v2/sandboxes/pr53?teamId=%s&projectId=%s' % (TEAM, PROJ))
    time.sleep(2)
    c, r = api_raw('POST', '/v4/sandboxes?teamId=%s' % TEAM,
                   {"projectId": PROJ, "name": 'pr53', "persistent": True})
    print('[r2 create persistent] -> %d %s' % (c, r[:200]), flush=True)
    if c == 200:
        d = json.loads(r)
        sid = d['sandbox']['currentSessionId']
        print('  persistent field:', json.dumps(d['sandbox'].get('persistent')), flush=True)
        time.sleep(8)
        c1, out1 = run_cmd(sid, "echo PR53-MARKER > /tmp/pr53.txt && cat /tmp/pr53.txt")
        print('[r2 marker] -> %d %s' % (c1, out1.strip()), flush=True)
        # PATCH persistent=false → 再 true → 看字段
        c2, r2 = api_raw('PATCH', '/v2/sandboxes/pr53?teamId=%s&projectId=%s' % (TEAM, PROJ), {"persistent": False})
        print('[r2 PATCH persistent=false] -> %d %s' % (c2, r2[:150]), flush=True)
        c3, r3 = api_raw('PATCH', '/v2/sandboxes/pr53?teamId=%s&projectId=%s' % (TEAM, PROJ), {"persistent": True})
        print('[r2 PATCH persistent=true] -> %d %s' % (c3, r3[:150]), flush=True)
        # 删除后 GET
        c4, r4 = api_raw('DELETE', '/v2/sandboxes/pr53?teamId=%s&projectId=%s' % (TEAM, PROJ))
        print('[r2 DELETE] -> %d' % c4, flush=True)
        time.sleep(3)
        c5, r5 = api_raw('GET', '/v2/sandboxes/pr53?teamId=%s&projectId=%s' % (TEAM, PROJ))
        print('[r2 GET after delete] -> %d %s' % (c5, r5[:150]), flush=True)
        c6, r6 = api_raw('GET', '/v2/sandboxes/pr53?teamId=%s&projectId=%s&resume=true' % (TEAM, PROJ))
        print('[r2 resume after delete] -> %d %s' % (c6, r6[:150]), flush=True)

    time.sleep(3)
    # ===== r3: PATCH runtime 切换 =====
    api_raw('DELETE', '/v2/sandboxes/rt2_53?teamId=%s&projectId=%s' % (TEAM, PROJ))
    time.sleep(2)
    c, r = api_raw('POST', '/v4/sandboxes?teamId=%s' % TEAM,
                   {"projectId": PROJ, "name": 'rt2_53', "runtime": 'node22'})
    print('[r3 create node22] -> %d %s' % (c, r[:150]), flush=True)
    if c == 200:
        sid = json.loads(r)['sandbox']['currentSessionId']
        time.sleep(8)
        c1, out1 = run_cmd(sid, "echo RT-MARK > /tmp/rt53.txt && cat /tmp/rt53.txt")
        print('[r3 marker] -> %d %s' % (c1, out1.strip()), flush=True)
        c2, r2 = api_raw('PATCH', '/v2/sandboxes/rt2_53?teamId=%s&projectId=%s' % (TEAM, PROJ), {"runtime": 'python3.13'})
        print('[r3 PATCH runtime=python3.13] -> %d %s' % (c2, r2[:150]), flush=True)
        time.sleep(3)
        c3, r3 = api_raw('GET', '/v2/sandboxes/rt2_53?teamId=%s&projectId=%s' % (TEAM, PROJ))
        print('[r3 GET after patch] -> %d %s' % (c3, r3[:250]), flush=True)
        api_raw('DELETE', '/v2/sandboxes/rt2_53?teamId=%s&projectId=%s' % (TEAM, PROJ))
    print('DONE', flush=True)

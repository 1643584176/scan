# -*- coding: utf-8 -*-
"""v51c: git source 拉取位置 + get-snapshot 详情 + fs/mkdir + drives 探测
G1: deny-all + git url (拉取方判定, 同 tarball 法)
G2: allow-all + git url (对照)
S1: GET /v2/sandboxes/snapshots/{id} (自己快照详情)
F1: POST fs/mkdir (新 fs 操作)
D1: POST /v2/sandboxes/drives/xxx (private beta 访问性)"""
import base64, json, sys, time, urllib.request, urllib.error
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, cmd, TOKEN, TEAM, PROJ

def api_raw(method, path, body=None, timeout=180, maxlen=200000):
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

def try_create(tag, name, body_extra, np_mode=None):
    body = {"projectId": PROJ, "name": name}
    body.update(body_extra)
    if np_mode:
        body["networkPolicy"] = {"mode": np_mode}
    c, r = api_raw('POST', '/v4/sandboxes?teamId=%s' % TEAM, body)
    print('[%s] -> %d %s' % (tag, c, (r or '')[:200]), flush=True)
    api_raw('DELETE', '/v2/sandboxes/%s?teamId=%s&projectId=%s' % (name, TEAM, PROJ))
    time.sleep(2)
    return c, r

def parse_data(r):
    out = ''
    for line in r.splitlines():
        if '"data"' in line:
            try:
                out += json.loads(line).get('data', '')
            except Exception:
                pass
    return out

if __name__ == '__main__':
    print('=== G1: deny-all + git ===', flush=True)
    try_create('G1', 'srcgit51a', {"source": {"type": "git", "url": "https://github.com/vercel/sandbox.git"}},
               np_mode='deny-all')
    print('=== G2: allow-all + git ===', flush=True)
    try_create('G2', 'srcgit51b', {"source": {"type": "git", "url": "https://github.com/vercel/sandbox.git"}})

    # S1: 需要先建快照
    print('=== S1: GET snapshot 详情 ===', flush=True)
    api_raw('DELETE', '/v2/sandboxes/snaps51?teamId=%s&projectId=%s' % (TEAM, PROJ))
    time.sleep(2)
    c, r = api_raw('POST', '/v4/sandboxes?teamId=%s' % TEAM, {"projectId": PROJ, "name": 'snaps51'})
    if c == 200:
        sid = json.loads(r)['sandbox']['currentSessionId']
        time.sleep(8)
        c2, r2 = api_raw('POST', '/v2/sandboxes/sessions/%s/snapshot?teamId=%s' % (sid, TEAM), {})
        print('[mk snap] -> %d %s' % (c2, (r2 or '')[:120]), flush=True)
        try:
            snap_id = json.loads(r2)['snapshot']['id']
            time.sleep(5)
            c3, r3 = api_raw('GET', '/v2/sandboxes/snapshots/%s?teamId=%s' % (snap_id, TEAM))
            print('[get snap detail] -> %d %s' % (c3, (r3 or '')[:400]), flush=True)
            # 清理快照
            api_raw('DELETE', '/v2/sandboxes/snapshots/%s?teamId=%s&project=%s' % (snap_id, TEAM, PROJ))
        except Exception as e:
            print('[get snap EXC] %s' % str(e)[:100], flush=True)
    api_raw('DELETE', '/v2/sandboxes/snaps51?teamId=%s&projectId=%s' % (TEAM, PROJ))

    # F1: fs/mkdir
    print('=== F1: fs/mkdir ===', flush=True)
    c, r = api_raw('POST', '/v4/sandboxes?teamId=%s' % TEAM, {"projectId": PROJ, "name": 'fsmk51'})
    if c == 200:
        sid = json.loads(r)['sandbox']['currentSessionId']
        time.sleep(8)
        for path in ['/tmp/mk_test_dir', '/vercel/mk_test', '/mk_root_test', '../mk_escape']:
            c2, r2 = api_raw('POST', '/v2/sandboxes/sessions/%s/fs/mkdir?teamId=%s' % (sid, TEAM), {"path": path})
            print('[mkdir %s] -> %d %s' % (path, c2, (r2 or '')[:100]), flush=True)
            time.sleep(1)
        # 验证
        b64 = base64.b64encode(b'ls -ld /tmp/mk_test_dir /vercel/mk_test /mk_root_test 2>&1').decode()
        c3, r3 = api_raw('POST', '/v2/sandboxes/sessions/%s/cmd?teamId=%s' % (sid, TEAM),
                         {"command": "sh", "args": ["-c", 'echo %s | base64 -d | sh' % b64],
                          "wait": True, "logs": True, "timeout": 15000}, timeout=60)
        print('[verify mkdir] -> %d %s' % (c3, parse_data(r3).strip()[:200]), flush=True)
        # 清理 mkdir 测试
        api_raw('POST', '/v2/sandboxes/sessions/%s/cmd?teamId=%s' % (sid, TEAM),
                {"command": "sh", "args": ["-c", 'rm -rf /tmp/mk_test_dir /vercel/mk_test /mk_root_test'],
                 "wait": True, "timeout": 15000}, timeout=60)
    api_raw('DELETE', '/v2/sandboxes/fsmk51?teamId=%s&projectId=%s' % (TEAM, PROJ))

    # D1: drives
    print('=== D1: drives 访问性 ===', flush=True)
    c, r = api_raw('POST', '/v2/sandboxes/drives/drv51?teamId=%s' % TEAM, {"projectId": PROJ})
    print('[create drive] -> %d %s' % (c, (r or '')[:200]), flush=True)
    c, r = api_raw('GET', '/v2/sandboxes/drives?teamId=%s&project=%s' % (TEAM, PROJ))
    print('[list drives] -> %d %s' % (c, (r or '')[:200]), flush=True)
    c, r = api_raw('DELETE', '/v2/sandboxes/drives/drv51?teamId=%s' % TEAM)
    print('[del drive] -> %d %s' % (c, (r or '')[:150]), flush=True)
    print('DONE', flush=True)

# -*- coding: utf-8 -*-
"""v54a: PATCH currentSnapshotId + deleteOrphanSnapshots 基线（自己账号正常语义）
SDK 源码发现的两个新参数路径"""
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

if __name__ == '__main__':
    name = 'snap54'
    api_raw('DELETE', '/v2/sandboxes/%s?teamId=%s&projectId=%s' % (name, TEAM, PROJ))
    time.sleep(2)
    c, r = api_raw('POST', '/v4/sandboxes?teamId=%s' % TEAM, {"projectId": PROJ, "name": name})
    if c != 200:
        print('create failed', r[:200], flush=True)
        sys.exit(1)
    sid = json.loads(r)['sandbox']['currentSessionId']
    print('sid =', sid, flush=True)
    time.sleep(8)

    # 1. 写 marker + 确认 alive
    c1, r1 = api_raw('POST', '/v2/sandboxes/sessions/%s/cmd?teamId=%s' % (sid, TEAM),
                     {"command": "bash", "args": ["-c", "echo SNAP54-MARKER > /tmp/snap54_marker.txt && cat /tmp/snap54_marker.txt"],
                      "wait": True, "logs": True, "timeout": 30000}, timeout=120)
    print('[marker] -> %d' % c1, flush=True)
    print(parse_data(r1).strip(), flush=True)

    # 2. POST snapshot → 自动 stop
    c2, r2 = api_raw('POST', '/v2/sandboxes/sessions/%s/snapshot?teamId=%s' % (sid, TEAM), {})
    print('[snapshot] -> %d %s' % (c2, r2[:300]), flush=True)
    snap = None
    if c2 == 201:
        snap = json.loads(r2).get('snapshotId') or json.loads(r2).get('id')
    if not snap and c2 == 201:
        snap = list(json.loads(r2).values())[0] if isinstance(json.loads(r2), dict) else None
    print('snap =', snap, flush=True)
    time.sleep(5)

    # 3. PATCH currentSnapshotId = 自己快照（基线）
    c3, r3 = api_raw('PATCH', '/v2/sandboxes/%s?teamId=%s&projectId=%s' % (name, TEAM, PROJ),
                     {"currentSnapshotId": snap})
    print('[PATCH currentSnapshotId self] -> %d %s' % (c3, r3[:400]), flush=True)

    # 4. resume → 检查 marker（快照恢复语义）
    c4, r4 = api_raw('GET', '/v2/sandboxes/%s?teamId=%s&projectId=%s&resume=true' % (name, TEAM, PROJ))
    print('[resume] -> %d' % c4, flush=True)
    nsid = None
    if c4 == 200:
        nsid = json.loads(r4)['sandbox'].get('currentSessionId')
        print('new sid =', nsid, ' currentSnapshotId =', json.loads(r4)['sandbox'].get('currentSnapshotId'), flush=True)
    time.sleep(8)
    if nsid:
        c5, r5 = api_raw('POST', '/v2/sandboxes/sessions/%s/cmd?teamId=%s' % (nsid, TEAM),
                         {"command": "bash", "args": ["-c", "cat /tmp/snap54_marker.txt 2>&1 || echo NO-MARKER"],
                          "wait": True, "logs": True, "timeout": 30000}, timeout=120)
        print('[marker after resume] -> %d' % c5, flush=True)
        print(parse_data(r5).strip(), flush=True)

    # 5. GET 快照详情全字段 + 列表
    c6, r6 = api_raw('GET', '/v2/sandboxes/snapshots/%s?teamId=%s' % (snap, TEAM))
    print('[snap detail] -> %d' % c6, flush=True)
    try:
        print(json.dumps(json.loads(r6), indent=1)[:800], flush=True)
    except Exception:
        print(r6[:500], flush=True)

    # 6. DELETE sandbox + deleteOrphanSnapshots=true（语义：孤儿快照是否被删）
    c7, r7 = api_raw('DELETE', '/v2/sandboxes/%s?teamId=%s&projectId=%s&deleteOrphanSnapshots=true' % (name, TEAM, PROJ))
    print('[DELETE + orphan] -> %d %s' % (c7, r7[:200]), flush=True)
    time.sleep(3)
    c8, r8 = api_raw('GET', '/v2/sandboxes/snapshots/%s?teamId=%s' % (snap, TEAM))
    print('[snap after delete+orphan] -> %d' % c8, flush=True)
    print(r8[:200], flush=True)
    # 清理残留快照
    if c8 == 200:
        api_raw('DELETE', '/v2/sandboxes/snapshots/%s?teamId=%s' % (snap, TEAM))
    print('DONE', flush=True)

# -*- coding: utf-8 -*-
"""v45d5: snapshot 201 停止后, resume 能否恢复? 恢复后数据是快照时刻?
流程: 创建 -> 写数据 -> snapshot -> 等 stopped -> 再写数据(应失败) -> resume -> 检查状态+数据"""
import base64, json, sys, time, urllib.request, urllib.error
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, cmd, TOKEN, TEAM, PROJ

NAME = 'snapresume49'

def api_raw(method, path, body=None, timeout=120):
    req = urllib.request.Request('https://api.vercel.com' + path, method=method)
    req.add_header('Authorization', 'Bearer ' + TOKEN)
    req.add_header('Content-Type', 'application/json')
    data = json.dumps(body).encode() if body is not None else None
    try:
        with urllib.request.urlopen(req, data=data, timeout=timeout) as r:
            return r.status, r.read().decode(errors='replace')[:800]
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode(errors='replace')[:800]
    except Exception as e:
        return -1, 'EXC %s' % str(e)[:120]

def mk():
    api("DELETE", "/v2/sandboxes/%s?teamId=%s&projectId=%s" % (NAME, TEAM, PROJ))
    time.sleep(3)
    for attempt in range(8):
        c, r = api("POST", "/v4/sandboxes?teamId=%s" % TEAM, {"projectId": PROJ, "name": NAME}, 60)
        if c == 429:
            print('[create] 429 retry', flush=True)
            time.sleep(20)
            continue
        break
    print('[create] -> %s' % c, flush=True)
    if c != 200:
        sys.exit(1)
    return json.loads(r)['sandbox']['currentSessionId']

def parse_data(r):
    out = ''
    for line in r.splitlines():
        if '"data"' in line:
            try:
                out += json.loads(line).get('data', '')
            except Exception:
                pass
    return out

def run_cmd(sid, script, tag):
    b64 = base64.b64encode(script).decode()
    try:
        c, r = cmd(sid, 'sh', ['-c', 'echo %s | base64 -d | sh' % b64], timeout_ms=15000)
        print('[%s] -> %d out=%r' % (tag, c, parse_data(r).strip()[:100]), flush=True)
        return c
    except Exception as e:
        print('[%s] -> EXC %s' % (tag, str(e)[:100]), flush=True)
        return -1

def get_status(tag):
    c, r = api('GET', '/v2/sandboxes/%s?teamId=%s&projectId=%s' % (NAME, TEAM, PROJ))
    try:
        d = json.loads(r)
        st = d['sandbox'].get('status')
        print('[%s] status=%s' % (tag, st), flush=True)
        return st
    except Exception:
        print('[%s GET] -> %d %s' % (tag, c, (r or '')[:120]), flush=True)
        return None

if __name__ == '__main__':
    sid = mk()
    print('sid =', sid, flush=True)
    time.sleep(10)

    # 1. 写快照前数据
    run_cmd(sid, b'echo BEFORE_SNAP_42 > /tmp/snap_data.txt; echo done', 'write-before')
    # 2. 快照
    c, r = api_raw('POST', '/v2/sandboxes/sessions/%s/snapshot?teamId=%s' % (sid, TEAM), {})
    print('[snapshot] -> %d %s' % (c, (r or '')[:150]), flush=True)
    # 3. 等 stopped
    time.sleep(10)
    get_status('after-snap')
    # 4. stopped 后写 (应失败)
    run_cmd(sid, b'echo AFTER_SNAP_77 > /tmp/snap_data2.txt', 'write-after')
    # 5. resume
    c, r = api('GET', '/v2/sandboxes/%s?teamId=%s&projectId=%s&resume=true' % (NAME, TEAM, PROJ), timeout=120)
    print('[resume] -> %d %s' % (c, (r or '')[:200]), flush=True)
    new_sid = None
    try:
        d = json.loads(r)
        new_sid = d['sandbox']['currentSessionId']
        print('  new sid =', new_sid, ' snap =', d['sandbox'].get('currentSnapshotId'), flush=True)
    except Exception:
        pass
    time.sleep(10)
    # 6. resume 后状态 + 数据检查 (必须用新 sid!)
    get_status('after-resume')
    sid2 = new_sid or sid
    run_cmd(sid2, b'echo "== before-file:"; cat /tmp/snap_data.txt 2>&1; echo "== after-file:"; cat /tmp/snap_data2.txt 2>&1', 'verify-data')

    api("DELETE", "/v2/sandboxes/%s?teamId=%s&projectId=%s" % (NAME, TEAM, PROJ))
    print('CLEANED', flush=True)

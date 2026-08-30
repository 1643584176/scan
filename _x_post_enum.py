# -*- coding: utf-8 -*-
"""POST/PATCH 端点枚举 + policy body 变体 (v45d)
P1: 枚举 session 下未测的 POST 子资源 (exec/restart/pause/kill/fs/snapshot/logs/...)
P2: network-policy 非法 body (mode=null/weird/空/类型错) -> 是否 fallback allow-all?
P3: cmd stale sessionId (stop 后旧 sid 是否仍可用)"""
import base64, json, sys, time
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, cmd, TEAM, PROJ

NAME = 'post45'

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

def cmd_sid(sid, command, args, timeout_ms=30000):
    """用指定 sessionId 调 cmd API"""
    body = {"command": command, "args": args, "wait": True, "logs": True, "timeout": timeout_ms}
    return api('POST', '/v2/sandboxes/sessions/%s/cmd?teamId=%s' % (sid, TEAM), body,
               timeout=timeout_ms / 1000 + 30)


if __name__ == '__main__':
    sid = mk()
    print('sid =', sid, flush=True)
    time.sleep(4)
    # ===== P1: POST 子资源枚举 =====
    print('=== P1: POST endpoint enum ===', flush=True)
    for p in ['/v2/sandboxes/sessions/%s/exec' % sid,
              '/v2/sandboxes/sessions/%s/exec-sync' % sid,
              '/v2/sandboxes/sessions/%s/execSync' % sid,
              '/v2/sandboxes/sessions/%s/restart' % sid,
              '/v2/sandboxes/sessions/%s/pause' % sid,
              '/v2/sandboxes/sessions/%s/resume' % sid,
              '/v2/sandboxes/sessions/%s/kill' % sid,
              '/v2/sandboxes/sessions/%s/snapshot' % sid,
              '/v2/sandboxes/sessions/%s/fs' % sid,
              '/v2/sandboxes/sessions/%s/fs/read' % sid,
              '/v2/sandboxes/sessions/%s/fs/write' % sid,
              '/v2/sandboxes/sessions/%s/upload' % sid,
              '/v2/sandboxes/sessions/%s/logs' % sid,
              '/v2/sandboxes/sessions/%s/events' % sid,
              '/v2/sandboxes/sessions/%s/stream' % sid,
              '/v2/sandboxes/sessions/%s/env' % sid,
              '/v2/sandboxes/sessions/%s/info' % sid,
              '/v2/sandboxes/%s/snapshot' % NAME,
              '/v2/sandboxes/%s/restart' % NAME,
              '/v2/sandboxes/%s/stop' % NAME]:
        c, r = api('POST', p + '?teamId=%s' % TEAM, {}, timeout=30)
        msg = (r or '')[:90].replace('\n', ' ')
        print('[POST %s] -> %d %s' % (p.split('/')[-1], c, msg), flush=True)
        time.sleep(0.8)
    # PATCH / PUT 变体
    c, r = api('PATCH', '/v2/sandboxes/%s?teamId=%s&projectId=%s' % (NAME, TEAM, PROJ), {"name": NAME}, 30)
    print('[PATCH sandbox] -> %d %s' % (c, (r or '')[:90]), flush=True)
    c, r = api('PUT', '/v2/sandboxes/%s?teamId=%s&projectId=%s' % (NAME, TEAM, PROJ), {}, 30)
    print('[PUT sandbox] -> %d %s' % (c, (r or '')[:90]), flush=True)

    # ===== P2: policy body 变体 =====
    print('=== P2: policy body variants ===', flush=True)
    for tag, body in [('mode-null', {"mode": None}),
                      ('mode-empty', {"mode": ""}),
                      ('mode-weird', {"mode": "weird-mode"}),
                      ('empty-obj', {}),
                      ('custom-str-domains', {"mode": "custom", "allowedDomains": "httpbin.org"}),
                      ('deny-with-domains', {"mode": "deny-all", "allowedDomains": ["httpbin.org"]})]:
        c, r = api('POST', '/v2/sandboxes/sessions/%s/network-policy?teamId=%s' % (sid, TEAM), body, timeout=30)
        print('[%s] -> %d %s' % (tag, c, (r or '')[:120]), flush=True)
        time.sleep(2)

    # ===== P3: cmd stale session =====
    print('=== P3: stale sessionId ===', flush=True)
    b64 = base64.b64encode(b'print("stale-test")').decode()
    c, r = cmd(NAME, 'sh', ['-c', 'echo %s | base64 -d | python3' % b64], timeout_ms=20000)
    print('[cmd current] -> %d' % c, flush=True)
    # stop -> resume 产生新 session
    c, r = api('POST', '/v2/sandboxes/sessions/%s/stop?teamId=%s&projectId=%s' % (sid, TEAM, PROJ), {}, timeout=90)
    print('[stop] -> %d' % c, flush=True)
    time.sleep(3)
    c, r = api('GET', '/v2/sandboxes/%s?teamId=%s&projectId=%s&resume=true' % (NAME, TEAM, PROJ), timeout=120)
    print('[resume] -> %d' % c, flush=True)
    time.sleep(8)
    # 用旧 sid 调 cmd
    c, r = cmd_sid(sid, 'sh', ['-c', 'echo %s | base64 -d | python3' % b64], timeout_ms=20000)
    print('[cmd old-sid] -> %d %s' % (c, (r or '')[:150]), flush=True)

    api("DELETE", "/v2/sandboxes/%s?teamId=%s&projectId=%s" % (NAME, TEAM, PROJ))
    print('CLEANED', flush=True)

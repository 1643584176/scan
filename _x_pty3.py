# -*- coding: utf-8 -*-
"""v46g 补跑: guest 内 23456/26661 端点枚举 (带 DNS 重试)"""
import base64, json, sys, time, urllib.request, urllib.error
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, cmd, TOKEN, TEAM, PROJ

NAME = 'ws46g2'

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

if __name__ == '__main__':
    sid = mk()
    print('sid =', sid, flush=True)
    time.sleep(12)
    b64 = base64.b64encode(
        b'for p in / /healthz /metrics /debug/pprof/ /api /v1 /version /info /ws /shell; do '
        b'echo "== 23456$p"; curl -s --max-time 2 http://127.0.0.1:23456$p 2>&1 | head -3; done; '
        b'echo "== 26661/"; curl -s --max-time 2 http://127.0.0.1:26661/ 2>&1 | head -3').decode()
    ok = False
    for i in range(6):
        try:
            c, r = cmd(sid, 'sh', ['-c', 'echo %s | base64 -d | sh' % b64], timeout_ms=40000)
            print('[probe try%d] -> %d' % (i + 1, c), flush=True)
            print(parse_data(r).strip()[:900], flush=True)
            ok = True
            break
        except Exception as e:
            print('[probe try%d EXC] %s' % (i + 1, str(e)[:120]), flush=True)
            time.sleep(15)
    api("DELETE", "/v2/sandboxes/%s?teamId=%s&projectId=%s" % (NAME, TEAM, PROJ))
    print('CLEANED' if ok else 'FAILED', flush=True)

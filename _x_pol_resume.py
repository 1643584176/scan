# -*- coding: utf-8 -*-
"""策略持久化: stop -> resume 后策略是否保持 (v44p)
bounty table: Medium "策略更新未持久化、resume 后失效"; Low "Policy 生命周期缺口"
流程: mk(带 custom) -> probe 基线 -> stop -> resume -> readback + probe"""
import base64, json, sys, time
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, cmd, TEAM, PROJ

NAME = 'poltest44'

def mk(with_policy):
    api("DELETE", "/v2/sandboxes/%s?teamId=%s&projectId=%s" % (NAME, TEAM, PROJ))
    time.sleep(3)
    body = {"projectId": PROJ, "name": NAME}
    if with_policy:
        body["networkPolicy"] = {"mode": "custom", "allowedDomains": ["httpbin.org"]}
    for attempt in range(8):
        c, r = api("POST", "/v4/sandboxes?teamId=%s" % TEAM, body, 60)
        if c == 429:
            print('[create] 429 retry %d' % (attempt + 1), flush=True)
            time.sleep(20)
            continue
        break
    print('[create policy=%s] -> %s' % (with_policy, c), flush=True)
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

PG_CODE = '''import socket,struct,time
s=socket.socket(); s.settimeout(4)
rc=s.connect_ex(('172.31.0.2',5432))
print('PG_CONNECT', rc)
if rc==0:
    s.sendall(struct.pack('!II',8,80877103))
    time.sleep(0.8)
    try:
        d=s.recv(4); print('PG_RESP', d)
    except Exception as e:
        print('PG_ERR', type(e).__name__)
'''

def probe(tag):
    b64 = base64.b64encode(PG_CODE.encode()).decode()
    c, r = cmd('poltest44', 'sh', ['-c', 'echo %s | base64 -d | python3' % b64], timeout_ms=30000)
    print('[%s] %s' % (tag, parse_data(r).strip()[:120]), flush=True)

def get_state(tag):
    c, r = api('GET', '/v2/sandboxes/%s?teamId=%s&projectId=%s' % (NAME, TEAM, PROJ))
    try:
        d = json.loads(r)
        sb, sess = d.get('sandbox', {}), d.get('session', {})
        print('[%s] status=%s sid=%s snap=%s' % (tag, sb.get('status'), sb.get('currentSessionId'), sb.get('currentSnapshotId')), flush=True)
        print('[%s] sandbox.networkPolicy=%s' % (tag, json.dumps(sb.get('networkPolicy'))), flush=True)
        print('[%s] session.networkPolicy=%s' % (tag, json.dumps(sess.get('networkPolicy'))), flush=True)
    except Exception as e:
        print('[%s ERR] %s %s' % (tag, c, (r or '')[:200]), flush=True)

if __name__ == '__main__':
    sid = mk(True)
    print('sid =', sid, flush=True)
    time.sleep(5)
    get_state('P1')
    probe('P1-custom')
    # stop
    c, r = api('POST', '/v2/sandboxes/sessions/%s/stop?teamId=%s&projectId=%s' % (sid, TEAM, PROJ), {}, timeout=90)
    print('[stop] -> %d %s' % (c, (r or '')[:250]), flush=True)
    time.sleep(3)
    get_state('P2-stopped')
    # resume: GET ?resume=true 尝试
    c, r = api('GET', '/v2/sandboxes/%s?teamId=%s&projectId=%s&resume=true' % (NAME, TEAM, PROJ), timeout=120)
    print('[resume GET] -> %d %s' % (c, (r or '')[:250]), flush=True)
    time.sleep(10)
    get_state('P3-resumed')
    probe('P3-resumed')
    # 清理
    api("DELETE", "/v2/sandboxes/%s?teamId=%s&projectId=%s" % (NAME, TEAM, PROJ))
    print('CLEANED', flush=True)

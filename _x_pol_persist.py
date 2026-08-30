# -*- coding: utf-8 -*-
"""策略持久化测试 (v44p): custom 策略 sandbox 删除重建后是否保持
判据: custom 模式 172.31.0.2:5432 可达(PG b'S') vs allow-all 基线 errno 113
readback 位置: sandbox.networkPolicy vs session.networkPolicy (绑定层级)"""
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
    d = json.loads(r)
    return d['sandbox']['currentSessionId']

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

def probe(sid, tag):
    b64 = base64.b64encode(PG_CODE.encode()).decode()
    c, r = cmd(sid, 'sh', ['-c', 'echo %s | base64 -d | python3' % b64], timeout_ms=30000)
    print('[%s] %s' % (tag, parse_data(r).strip()[:120]), flush=True)

def readback(tag):
    c, r = api('GET', '/v2/sandboxes/%s?teamId=%s&projectId=%s' % (NAME, TEAM, PROJ))
    try:
        d = json.loads(r)
        sb = d.get('sandbox', {})
        sess = d.get('session', {})
        print('[%s readback] sandbox.networkPolicy=%s' % (tag, json.dumps(sb.get('networkPolicy'))), flush=True)
        print('[%s readback] session.networkPolicy=%s' % (tag, json.dumps(sess.get('networkPolicy'))), flush=True)
        print('[%s readback] sandbox keys=%s' % (tag, sorted(sb.keys())), flush=True)
        print('[%s readback] session keys=%s' % (tag, sorted(sess.keys())), flush=True)
    except Exception as e:
        print('[%s readback ERR] %s %s' % (tag, c, (r or '')[:200]), flush=True)

if __name__ == '__main__':
    sid = mk(True)
    print('P1 sid =', sid, flush=True)
    time.sleep(5)
    readback('P1')
    probe(sid, 'P1-custom')
    # 删除重建 (无策略)
    api("DELETE", "/v2/sandboxes/%s?teamId=%s&projectId=%s" % (NAME, TEAM, PROJ))
    time.sleep(4)
    sid2 = mk(False)
    print('P2 sid =', sid2, flush=True)
    time.sleep(5)
    readback('P2')
    probe(sid2, 'P2-recreated')
    # 清理
    api("DELETE", "/v2/sandboxes/%s?teamId=%s&projectId=%s" % (NAME, TEAM, PROJ))
    print('CLEANED', flush=True)

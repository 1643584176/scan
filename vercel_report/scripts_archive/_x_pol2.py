# -*- coding: utf-8 -*-
"""P 线实验 2: 运行时策略切换 -> stop -> resume -> 策略是否保持 (核心场景)"""
import json, sys, time
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, cmd, TEAM, PROJ

def conn_test(sid, tag):
    script = 'python3 -c "import socket; s=socket.socket(); s.settimeout(4); rc=s.connect_ex((\'1.1.1.1\',443)); print(\'PUB_RC\', rc)"'
    c, r = cmd(sid, 'sh', ['-c', script], timeout_ms=30000)
    pub = '?'
    try:
        pub = r.split('PUB_RC')[-1].strip()[:10]
    except Exception:
        pass
    script2 = 'python3 -c "import socket; s=socket.socket(); s.settimeout(4); rc=s.connect_ex((\'httpbin.org\',443)); print(\'HTTPBIN_RC\', rc)"'
    c2, r2 = cmd(sid, 'sh', ['-c', script2], timeout_ms=30000)
    hb = '?'
    try:
        hb = r2.split('HTTPBIN_RC')[-1].strip()[:10]
    except Exception:
        pass
    print('[%s] PUB_443=%s HTTPBIN_443=%s' % (tag, pub, hb), flush=True)
    return pub, hb

def get_policy(name):
    c, r = api('GET', '/v2/sandboxes/%s?teamId=%s&projectId=%s' % (name, TEAM, PROJ))
    if c != 200:
        print('get %s -> %d %s' % (name, c, r[:200]), flush=True)
        return None, None, None
    d = json.loads(r)
    sb = d.get('sandbox', {})
    sess = d.get('session', {})
    return sb.get('status'), sb.get('networkPolicy'), sess.get('networkPolicy')

def set_policy(sid, mode, domains=None):
    body = {'mode': mode}
    if domains:
        body['allowedDomains'] = domains
    c, r = api('POST', '/v2/sandboxes/sessions/%s/network-policy?teamId=%s' % (sid, TEAM), body)
    print('set_policy %s -> %d %s' % (mode, c, r[:150]), flush=True)
    time.sleep(2)
    return c

# ============ 场景 2: 创建默认(allow-all) -> 运行时切 deny-all -> stop -> resume ============
print('===== S2: default create, runtime deny-all, resume =====', flush=True)
name2 = 'ppol2'
api('DELETE', '/v2/sandboxes/%s?teamId=%s&projectId=%s' % (name2, TEAM, PROJ))
time.sleep(2)
c, r = api('POST', '/v2/sandboxes?teamId=%s' % TEAM, {"projectId": PROJ, "name": name2})
print('create:', c, r[:150], flush=True)
sid2 = json.loads(r)['sandbox']['currentSessionId']
time.sleep(3)
st, sbp, sep = get_policy(name2)
print('S2 after create: status=%s sandbox_pol=%s session_pol=%s' % (st, json.dumps(sbp), json.dumps(sep)), flush=True)
conn_test(sid2, 'S2-create-default')

set_policy(sid2, 'deny-all')
st, sbp, sep = get_policy(name2)
print('S2 after runtime deny-all: sandbox_pol=%s session_pol=%s' % (json.dumps(sbp), json.dumps(sep)), flush=True)
conn_test(sid2, 'S2-runtime-denyall')

c, r = api('POST', '/v2/sandboxes/sessions/%s/stop?teamId=%s' % (sid2, TEAM))
print('S2 stop:', c, flush=True)
time.sleep(3)
st, sbp, sep = get_policy(name2)
print('S2 after stop: status=%s sandbox_pol=%s session_pol=%s' % (st, json.dumps(sbp), json.dumps(sep)), flush=True)

c, r = api('GET', '/v2/sandboxes/%s?teamId=%s&projectId=%s&resume=true' % (name2, TEAM, PROJ))
print('S2 resume:', c, flush=True)
if c == 200:
    d = json.loads(r)
    sid2 = d['sandbox']['currentSessionId']
    time.sleep(3)
    st, sbp, sep = get_policy(name2)
    print('S2 after resume: status=%s sandbox_pol=%s session_pol=%s' % (st, json.dumps(sbp), json.dumps(sep)), flush=True)
    conn_test(sid2, 'S2-resume')

print('=== P2 DONE ===', flush=True)

# -*- coding: utf-8 -*-
"""P 线实验: 策略持久化/生命周期缺口
场景1: 创建时 deny-all -> stop -> resume -> 检查策略是否保持
场景2: 创建时默认(allow-all) -> 运行时切 deny-all -> stop -> resume -> 检查
"""
import json, sys, time
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, cmd, TEAM, PROJ

def conn_test(sid, tag):
    """沙箱内实测出网: 1.1.1.1(443) 与 httpbin.org(443)"""
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

# ============ 场景 1: 创建时 deny-all ============
print('===== S1: create deny-all =====', flush=True)
name1 = 'ppol1'
api('DELETE', '/v2/sandboxes/%s?teamId=%s&projectId=%s' % (name1, TEAM, PROJ))
time.sleep(2)
c, r = api('POST', '/v2/sandboxes?teamId=%s' % TEAM, {"projectId": PROJ, "name": name1, "networkPolicy": {"mode": "deny-all"}})
print('create:', c, r[:200], flush=True)
sid1 = json.loads(r)['sandbox']['currentSessionId']
time.sleep(3)
st, sbp, sep = get_policy(name1)
print('S1 after create: status=%s sandbox_pol=%s session_pol=%s' % (st, json.dumps(sbp), json.dumps(sep)), flush=True)
conn_test(sid1, 'S1-create-denyall')

# 停止
c, r = api('POST', '/v2/sandboxes/sessions/%s/stop?teamId=%s' % (sid1, TEAM))
print('S1 stop:', c, r[:200], flush=True)
time.sleep(3)
st, sbp, sep = get_policy(name1)
print('S1 after stop: status=%s sandbox_pol=%s session_pol=%s' % (st, json.dumps(sbp), json.dumps(sep)), flush=True)

# resume
c, r = api('GET', '/v2/sandboxes/%s?teamId=%s&projectId=%s&resume=true' % (name1, TEAM, PROJ))
print('S1 resume:', c, r[:200], flush=True)
if c == 200:
    d = json.loads(r)
    sid1 = d['sandbox']['currentSessionId']
    time.sleep(3)
    st, sbp, sep = get_policy(name1)
    print('S1 after resume: status=%s sandbox_pol=%s session_pol=%s' % (st, json.dumps(sbp), json.dumps(sep)), flush=True)
    conn_test(sid1, 'S1-resume')

print('=== P1 DONE ===', flush=True)

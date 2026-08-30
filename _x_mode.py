# -*- coding: utf-8 -*-
"""P 线实验 3: default-allow / default-deny 模式实际行为 + stale readback 检查"""
import json, re, sys, time
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, cmd, TEAM, PROJ

def probe(sid, ip, port, tag):
    sc = 'python3 -c "import socket; s=socket.socket(); s.settimeout(4); rc=s.connect_ex((\'%s\',%d)); print(\'RC_\', rc)"' % (ip, port)
    c, r = cmd(sid, 'sh', ['-c', sc], timeout_ms=30000)
    rc = '?'
    try:
        for line in r.splitlines():
            if '"data"' in line:
                d = json.loads(line).get('data', '')
                m = re.search(r'RC_ (\d+)', d)
                if m:
                    rc = m.group(1)
    except Exception:
        pass
    print('[%s] %s:%d -> %s' % (tag, ip, port, rc), flush=True)
    return rc

def run_case(name, mode, extra=None):
    print('===== case %s mode=%s =====' % (name, mode), flush=True)
    api('DELETE', '/v2/sandboxes/%s?teamId=%s&projectId=%s' % (name, TEAM, PROJ))
    time.sleep(2)
    body = {"projectId": PROJ, "name": name, "networkPolicy": {"mode": mode}}
    if extra:
        body['networkPolicy'].update(extra)
    c, r = api('POST', '/v2/sandboxes?teamId=%s' % TEAM, body)
    print('create:', c, r[:150], flush=True)
    if c != 200:
        print('CREATE_FAIL:', r[:300], flush=True)
        return None
    d = json.loads(r)
    sid = d['sandbox']['currentSessionId']
    time.sleep(3)
    # readback
    c2, r2 = api('GET', '/v2/sandboxes/%s?teamId=%s&projectId=%s' % (name, TEAM, PROJ))
    try:
        d2 = json.loads(r2)
        print('readback sandbox_pol:', json.dumps(d2['sandbox'].get('networkPolicy')), flush=True)
        print('readback session_pol:', json.dumps(d2.get('session', {}).get('networkPolicy')), flush=True)
    except Exception:
        print('readback err:', r2[:200], flush=True)
    # 实测
    probe(sid, '1.1.1.1', 443, name + '-pub')
    probe(sid, '172.31.0.2', 5432, name + '-vpc')
    probe(sid, '8.8.8.8', 53, name + '-dns')
    return sid

run_case('dmode1', 'default-allow')
run_case('dmode2', 'default-deny')
run_case('dmode3', 'custom', {'allowedDomains': ['httpbin.org'], 'allowedCIDRs': ['10.0.0.0/8']})

print('=== MODE DONE ===', flush=True)

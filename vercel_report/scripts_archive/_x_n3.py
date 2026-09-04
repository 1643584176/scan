# -*- coding: utf-8 -*-
"""独立根因候选2: 项目 OIDC 已启用(enabled=true, issuerMode=team), 沙箱 guest 是否注入真实 VERCEL_OIDC_TOKEN?
合规: 只做存在性+JWT metadata 确认 (stop at confirmation), 不打印完整 token, 不用 token 访问任何资源"""
import json, sys, time, base64
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, TEAM, PROJ

def log(s): print(s, flush=True)

def run_cmd(sid, command, args, timeout_ms=30000):
    c, r = api("POST", "/v2/sandboxes/sessions/%s/cmd?teamId=%s" % (sid, TEAM),
               {"command": command, "args": args, "wait": True, "logs": True, "timeout": timeout_ms})
    out = ''
    for line in r.splitlines():
        if '"data"' in line:
            try: out += json.loads(line).get('data', '')
            except Exception: pass
    return c, out

def b64d(s):
    s += '=' * (-len(s) % 4)
    return base64.urlsafe_b64decode(s).decode('utf-8', 'replace')

# 1) 创建沙箱 (无 env)
c, r = api("POST", "/v2/sandboxes?teamId=%s" % TEAM, {"projectId": PROJ, "name": "n3"})
if c != 200:
    log('create failed: %s' % r[:200]); sys.exit(1)
sid = json.loads(r)["sandbox"]["currentSessionId"]
log('n3 sid: %s' % sid)
time.sleep(3)

# 2) guest 检查 OIDC token
log('')
log('===== guest VERCEL_* check =====')
c2, out = run_cmd(sid, 'sh', ['-c', 'env | grep "^VERCEL_" | cut -d= -f1 | sort'], 20000)
log('VERCEL_ names: [%s]' % out.strip())
c2, out = run_cmd(sid, 'sh', ['-c', 'echo "OIDC len=${#VERCEL_OIDC_TOKEN}"; echo "OIDC head=${VERCEL_OIDC_TOKEN:0:30}"'], 20000)
log(out.strip()[:400])

# 3) 若有 token: JWT metadata (alg/iss/aud/exp), 不打印完整 token
if 'VERCEL_OIDC_TOKEN' in run_cmd(sid, 'sh', ['-c', 'env | grep -c "^VERCEL_OIDC_TOKEN="'], 15000)[1]:
    c3, out = run_cmd(sid, 'sh', ['-c', 'echo "$VERCEL_OIDC_TOKEN" | cut -d. -f1,2'], 15000)
    parts = out.strip().split('.')
    if len(parts) >= 2:
        try:
            hdr = json.loads(b64d(parts[0]))
            claims = json.loads(b64d(parts[1]))
            log('JWT header: %s' % json.dumps(hdr))
            meta = {k: claims.get(k) for k in ['iss', 'sub', 'aud', 'exp', 'iat', 'team_id', 'project_id'] if k in claims}
            log('JWT claims(meta only): %s' % json.dumps(meta)[:400])
        except Exception as e:
            log('JWT parse fail: %s' % e)
    else:
        log('not a JWT (len=%d, head=%s)' % (len(out.strip()), out.strip()[:40]))

api("DELETE", "/v2/sandboxes/n3?teamId=%s&projectId=%s" % (TEAM, PROJ))
log('DONE')

# -*- coding: utf-8 -*-
"""四线: (1) interactivePort/网络接口/监听面 (2) 快照全字段+restore 端点 (3) 跨租户/坏 ID 校验 (4) sandbox-init 精准字符串"""
import json, sys, time, base64
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, TEAM, PROJ, BASE, TOKEN

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

c, r = api("POST", "/v2/sandboxes?teamId=%s" % TEAM, {"projectId": PROJ, "name": "loc7"})
if c != 200:
    log('create failed: %s' % r[:200]); sys.exit(1)
d = json.loads(r)
sid = d["sandbox"]["currentSessionId"]
log('loc7 sid: %s' % sid)
log('session keys: %s' % sorted(d.get('session', {}).keys()))
for k, v in d.get('session', {}).items():
    log('  se.%s = %s' % (k, json.dumps(v)[:150]))
time.sleep(3)

# 1) 网络接口 + 监听面
log('')
log('===== 1) net iface/listeners =====')
c2, out = run_cmd(sid, 'sh', ['-c', 'ip addr 2>/dev/null || ifconfig 2>/dev/null; echo ===; cat /proc/net/tcp /proc/net/tcp6 | grep -E "0A$|0B$|0C$" ; echo ===; cat /etc/resolv.conf 2>/dev/null; echo ===; ip route 2>/dev/null'], 30000)
log(out[:2500])

# 2) 快照全字段 + restore 端点
log('')
log('===== 2) snapshot fields + restore =====')
c3, r3 = api("GET", "/v2/sandboxes/snapshots?teamId=%s&project=%s&limit=2" % (TEAM, PROJ))
if c3 == 200:
    snaps = json.loads(r3).get('snapshots', [])
    if snaps:
        snid = snaps[0].get('id')
        log('snap fields: %s' % sorted(snaps[0].keys()))
        for k, v in snaps[0].items():
            log('  %s = %s' % (k, json.dumps(v)[:200]))
        for path in [
            "/v2/sandboxes/snapshots/%s/restore?teamId=%s" % (snid, TEAM),
            "/v2/sandboxes/snapshots/%s/apply?teamId=%s" % (snid, TEAM),
            "/v2/sandboxes/snapshots/%s/clone?teamId=%s" % (snid, TEAM),
            "/v2/sandboxes/snapshots/%s/promote?teamId=%s" % (snid, TEAM),
            "/v2/sandboxes/snapshots/%s/rollback?teamId=%s" % (snid, TEAM),
        ]:
            c4, r4 = api("POST", path, {})
            log('POST %s -> %s | %s' % (path.split('/')[-2] + '/' + path.split('/')[-1], c4, r4[:200].replace('\n', ' ')))

# 3) 跨租户/坏 ID 校验
log('')
log('===== 3) cross-tenant / bad-id checks =====')
# 格式正确但不存在的 ID
for p in [
    "/v2/sandboxes?teamId=team_0000000000000000000000000",
    "/v2/sandboxes?teamId=team_%s" % TEAM,
]:
    c4, r4 = api("GET", p)
    log('GET %s -> %s | %s' % (p[:60], c4, r4[:200].replace('\n', ' ')))
# 用坏 projectId 创建
c4, r4 = api("POST", "/v2/sandboxes?teamId=%s" % TEAM, {"projectId": "prj_0000000000000000000000000", "name": "xbad"})
log('create bad proj -> %s | %s' % (c4, r4[:250].replace('\n', ' ')))
# 坏 teamId 创建
c4, r4 = api("POST", "/v2/sandboxes?teamId=team_0000000000000000000000000", {"projectId": PROJ, "name": "xbad2"})
log('create bad team -> %s | %s' % (c4, r4[:250].replace('\n', ' ')))

# 4) sandbox-init 精准字符串
log('')
log('===== 4) sandbox-init biz strings =====')
ST = '''import re
data = open('/run/vercel/share/sandbox-init','rb').read()
seen = set()
pats = ['vercel.com','vercel.internal','.internal','sbx_','sandbox','session','/cmd','/fs/','/exec','interactive','attach','pty','/api/','/v2/','oidc','token','secret','key=','password','authorization','/run/','share/','sock','websocket','grpc','http2','hostname','127.0.0.1','localhost',':23456',':26661',':40532',':47354']
for m in re.finditer(rb'[\\x20-\\x7e]{5,}', data):
    s = m.group().decode(errors='replace')
    low = s.lower()
    if '/usr/local/go' in s or '/go/src' in s:
        continue
    if any(p.lower() in low for p in pats) and len(s) < 200:
        if s not in seen:
            seen.add(s)
            print(s)
'''
b64 = base64.b64encode(ST.encode()).decode()
c2, out = run_cmd(sid, 'sh', ['-c', 'echo %s | base64 -d | python3' % b64], 90000)
log(out[-5000:])

api("DELETE", "/v2/sandboxes/loc7?teamId=%s&projectId=%s" % (TEAM, PROJ))
log('DONE')

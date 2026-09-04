# -*- coding: utf-8 -*-
"""四线: (1) v1 沙箱清理 (2) PATCH runtime 生效验证 (3) v1 networkPolicy 对比 (4) PATCH 配额字段 (vcpus/memory/timeout)"""
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

# 1) v1 沙箱列表 + 清理
log('')
log('===== 1) v1 sandbox cleanup =====')
c3, r3 = api("GET", "/v1/sandboxes?teamId=%s&project=%s&limit=20" % (TEAM, PROJ))
log('v1 list -> %s | %s' % (c3, r3[:800].replace('\n', ' ')))
if c3 == 200:
    try:
        lst = json.loads(r3).get('sandboxes', [])
        for sb in lst:
            log('  v1 sb: id=%s runtime=%s status=%s' % (sb.get('id'), sb.get('runtime'), sb.get('status')))
    except Exception as e:
        log('  parse err %s' % e)
# 试删除 v1 沙箱
for path in [
    "/v1/sandboxes/sbx_oo0SgYD5mo1GvSkn4jJwovaQptSH?teamId=%s&projectId=%s" % (TEAM, PROJ),
    "/v1/sandboxes/sbx_oo0SgYD5mo1GvSkn4jJwovaQptSH?teamId=%s" % TEAM,
]:
    c3, r3 = api("DELETE", path)
    log('DELETE v1 -> %s | %s' % (c3, r3[:150].replace('\n', ' ')))

# 2) PATCH runtime 生效验证
log('')
log('===== 2) PATCH runtime effect =====')
c, r = api("POST", "/v2/sandboxes?teamId=%s" % TEAM, {"projectId": PROJ, "name": "loc14"})
if c != 200:
    log('create failed: %s' % r[:200]); sys.exit(1)
sid = json.loads(r)["sandbox"]["currentSessionId"]
log('loc14 sid: %s' % sid)
# PATCH runtime
c3, r3 = api("PATCH", "/v2/sandboxes/loc14?teamId=%s&projectId=%s" % (TEAM, PROJ), {"runtime": "python3.13"})
log('PATCH runtime=python3.13 -> %s | %s' % (c3, r3[:300].replace('\n', ' ')))
# GET 确认 runtime 字段
c4, r4 = api("GET", "/v2/sandboxes/loc14?teamId=%s&projectId=%s" % (TEAM, PROJ))
if c4 == 200:
    d = json.loads(r4)
    log('GET runtime=%s persistent=%s' % (d.get('sandbox', {}).get('runtime'), d.get('sandbox', {}).get('persistent')))
# 非法 runtime
c3, r3 = api("PATCH", "/v2/sandboxes/loc14?teamId=%s&projectId=%s" % (TEAM, PROJ), {"runtime": "totally-fake"})
log('PATCH runtime=fake -> %s | %s' % (c3, r3[:250].replace('\n', ' ')))
# resume 后 guest 内验证
time.sleep(2)
c2, out = run_cmd(sid, 'sh', ['-c', 'python3 --version 2>&1; node --version 2>&1'], 20000)
log('guest versions: %s' % out[:300])

# 3) v1 networkPolicy 对比
log('')
log('===== 3) v1 networkPolicy =====')
c3, r3 = api("POST", "/v1/sandboxes?teamId=%s" % TEAM,
             {"projectId": PROJ, "networkPolicy": {"mode": "custom", "allowedDomains": ["httpbin.org"]}})
log('POST v1 custom -> %s | %s' % (c3, r3[:300].replace('\n', ' ')))
if c3 == 200:
    d = json.loads(r3)
    vid = d.get('sandbox', {}).get('id')
    log('v1 custom sandbox id: %s' % vid)
    if vid:
        # 测 5432 连通性
        time.sleep(3)
        PG = '''import socket
for ip in ['172.31.0.2']:
    s=socket.socket(); s.settimeout(3)
    rc=s.connect_ex((ip,5432))
    print(ip, 'RC', rc, flush=True)
    s.close()
'''
        b64 = base64.b64encode(PG.encode()).decode()
        c2, out = run_cmd(vid, 'sh', ['-c', 'echo %s | base64 -d | python3' % b64], 30000)
        log('v1 custom pg: %s' % out[:300])
        # v1 沙箱名清理: 从 v2 列表找
        c4, r4 = api("GET", "/v2/sandboxes?teamId=%s&project=%s&limit=50" % (TEAM, PROJ))
        if c4 == 200:
            for sb in json.loads(r4).get('sandboxes', []):
                if sb.get('currentSessionId') == vid:
                    log('v1 sandbox name in v2: %s' % sb.get('name'))
                    api("DELETE", "/v2/sandboxes/%s?teamId=%s&projectId=%s" % (sb.get('name'), TEAM, PROJ))
                    break
        # 兜底: 直接试 v1 delete by id
        api("DELETE", "/v1/sandboxes/%s?teamId=%s&projectId=%s" % (vid, TEAM, PROJ))

# 4) PATCH 配额字段
log('')
log('===== 4) PATCH quota fields =====')
for body in [
    {"vcpus": 8},
    {"memory": 8192},
    {"timeout": 900000},
    {"persistent": False},
    {"env": {"FOO": "bar"}},
]:
    c3, r3 = api("PATCH", "/v2/sandboxes/loc14?teamId=%s&projectId=%s" % (TEAM, PROJ), body)
    log('PATCH %-14s -> %s | %s' % (list(body.keys())[0], c3, r3[:200].replace('\n', ' ')))

api("DELETE", "/v2/sandboxes/loc14?teamId=%s&projectId=%s" % (TEAM, PROJ))
log('DONE')

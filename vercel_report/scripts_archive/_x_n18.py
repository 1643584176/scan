# -*- coding: utf-8 -*-
"""非传统面C: projectId 可选语义 — 跨项目同名沙箱的 GET/DELETE/PATCH 作用域混淆
正常流程总是带 projectId; 不传时按什么作用域? 同名冲突会误操作哪个项目?"""
import json, sys, time
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, TEAM, PROJ

def log(s): print(s, flush=True)

# 1) 建第二项目
c, r = api("POST", "/v9/projects?teamId=%s" % TEAM, {"name": "sec-lab-2"}, 40)
log('create proj2 -> %s | %s' % (c, (r[:250] if r else '').replace(chr(10), ' ')))
if c != 200 and c != 201:
    log('proj2 create fail, exit'); sys.exit(1)
try:
    proj2 = json.loads(r).get('project', {}).get('id') or json.loads(r).get('id')
except Exception:
    proj2 = None
log('proj2=%s' % proj2)
time.sleep(2)

# 2) 两项目同名沙箱
for pname, pid in [('proj1', PROJ), ('proj2', proj2)]:
    api("DELETE", "/v2/sandboxes/dup?teamId=%s&projectId=%s" % (TEAM, pid))
    time.sleep(1)
    c, r = api("POST", "/v4/sandboxes?teamId=%s" % TEAM, {"projectId": pid, "name": "dup"}, 60)
    log('%s dup create -> %s' % (pname, c))
    time.sleep(2)

# 3) 无 projectId 的 GET/PATCH/DELETE
log('')
log('===== 无 projectId 操作 =====')
c, r = api("GET", "/v2/sandboxes/dup?teamId=%s" % TEAM, None, 20)
log('GET dup (no proj) -> %s | %s' % (c, (r[:250] if r else '').replace(chr(10), ' ')))
c, r = api("GET", "/v2/sandboxes/dup?teamId=%s&projectId=%s" % (TEAM, PROJ), None, 20)
log('GET dup (proj1) -> %s | %s' % (c, (r[:150] if r else '').replace(chr(10), ' ')))
if proj2:
    c, r = api("GET", "/v2/sandboxes/dup?teamId=%s&projectId=%s" % (proj2 and TEAM, proj2), None, 20)
    log('GET dup (proj2) -> %s | %s' % (c, (r[:150] if r else '').replace(chr(10), ' ')))

# PATCH 无 projectId (改 runtime 作为探针)
c, r = api("PATCH", "/v2/sandboxes/dup?teamId=%s" % TEAM, {"timeout": 999999}, 20)
log('PATCH dup (no proj) -> %s | %s' % (c, (r[:200] if r else '').replace(chr(10), ' ')))
# 看哪个项目的 dup 被改了
for pname, pid in [('proj1', PROJ), ('proj2', proj2)]:
    c, r = api("GET", "/v2/sandboxes/dup?teamId=%s&projectId=%s" % (TEAM, pid), None, 20)
    if c == 200:
        try:
            to = json.loads(r).get('sandbox', {}).get('timeout')
            log('%s dup timeout now: %s' % (pname, to))
        except Exception: pass

# DELETE 无 projectId
c, r = api("DELETE", "/v2/sandboxes/dup?teamId=%s" % TEAM, None, 20)
log('DELETE dup (no proj) -> %s | %s' % (c, (r[:150] if r else '').replace(chr(10), ' ')))
for pname, pid in [('proj1', PROJ), ('proj2', proj2)]:
    c, r = api("GET", "/v2/sandboxes/dup?teamId=%s&projectId=%s" % (TEAM, pid), None, 20)
    log('%s dup after del -> %s' % (pname, c))

# 4) 清理
for pname, pid in [('proj1', PROJ), ('proj2', proj2)]:
    api("DELETE", "/v2/sandboxes/dup?teamId=%s&projectId=%s" % (TEAM, pid))
if proj2:
    c, r = api("DELETE", "/v9/projects/%s?teamId=%s" % (proj2, TEAM), None, 30)
    log('del proj2 -> %s' % c)
log('DONE')

# -*- coding: utf-8 -*-
"""非传统面B: 流程破坏 — ①删沙箱重建同名, 旧 sid 是否指向新沙箱 ②已删沙箱的快照跨删除恢复
正常流程不会: 删除后用旧引用操作新对象"""
import json, sys, time
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, TEAM, PROJ

def log(s): print(s, flush=True)

# 1) 建 A + 标记文件
api("DELETE", "/v2/sandboxes/n17a?teamId=%s&projectId=%s" % (TEAM, PROJ))
time.sleep(2)
c, r = api("POST", "/v4/sandboxes?teamId=%s" % TEAM, {"projectId": PROJ, "name": "n17a"}, 60)
if c != 200:
    log('create A fail %s' % r[:200]); sys.exit(1)
d = json.loads(r)['sandbox']
sidA = d['currentSessionId']
log('A sid=%s' % sidA)
time.sleep(3)
c, r = api("POST", "/v2/sandboxes/sessions/%s/cmd?teamId=%s" % (sidA, TEAM),
           {"command": "sh", "args": ["-c", "echo MARKER_A_2026 > /tmp/marker.txt && cat /tmp/marker.txt"],
            "wait": True, "timeout": 10000}, 25)
log('A marker -> %s' % c)

# 2) stop (自动快照)
c, r = api("POST", "/v2/sandboxes/sessions/%s/stop?teamId=%s" % (sidA, TEAM), {}, 25)
snapA = None
if c == 200:
    try: snapA = json.loads(r).get('sandbox', {}).get('currentSnapshotId')
    except Exception: pass
log('A stop snap=%s' % snapA)
time.sleep(2)

# 3) DELETE A
c, r = api("DELETE", "/v2/sandboxes/n17a?teamId=%s&projectId=%s" % (TEAM, PROJ))
log('A delete -> %s' % c)
time.sleep(3)

# 4) 重建同名 A' → 用旧 sid 操作
log('')
log('===== ① 重建同名, 旧 sid 引用 =====')
c, r = api("POST", "/v4/sandboxes?teamId=%s" % TEAM, {"projectId": PROJ, "name": "n17a"}, 60)
if c != 200:
    log('recreate A fail %s' % r[:200])
else:
    d2 = json.loads(r)['sandbox']
    sidA2 = d2['currentSessionId']
    log("A' sid=%s (new)" % sidA2)
    time.sleep(3)
    c, r = api("POST", "/v2/sandboxes/sessions/%s/cmd?teamId=%s" % (sidA, TEAM),
               {"command": "cat", "args": ["/tmp/marker.txt"], "wait": True, "timeout": 8000}, 20)
    log('old-sid cmd on new sandbox -> %s | %s' % (c, (r[:150] if r else '').replace(chr(10), ' ')))
    c, r = api("POST", "/v2/sandboxes/sessions/%s/fs/read?teamId=%s" % (sidA, TEAM), {"path": "/tmp/marker.txt"}, 20)
    log('old-sid fs on new sandbox -> %s | %s' % (c, (r[:150] if r else '').replace(chr(10), ' ')))
    c, r = api("POST", "/v2/sandboxes/sessions/%s/interactive?teamId=%s" % (sidA, TEAM), {}, 15)
    log('old-sid interactive -> %s | %s' % (c, (r[:150] if r else '').replace(chr(10), ' ')))
    # 新沙箱 fs 对照 (不应有 marker)
    c, r = api("POST", "/v2/sandboxes/sessions/%s/fs/read?teamId=%s" % (sidA2, TEAM), {"path": "/tmp/marker.txt"}, 20)
    log('new-sid fs marker (expect 404) -> %s | %s' % (c, (r[:120] if r else '').replace(chr(10), ' ')))

# 5) 用已删沙箱的快照恢复 (v4 source=snapshot)
log('')
log('===== ② 已删沙箱快照恢复 =====')
if snapA:
    c, r = api("POST", "/v4/sandboxes?teamId=%s" % TEAM,
               {"projectId": PROJ, "name": "n17b",
                "source": {"type": "snapshot", "snapshotId": snapA}}, 90)
    log('restore deleted-sandbox snapshot -> %s | %s' % (c, (r[:250] if r else '').replace(chr(10), ' ')))
    if c == 200:
        sidB = json.loads(r)['sandbox']['currentSessionId']
        time.sleep(4)
        c, r = api("POST", "/v2/sandboxes/sessions/%s/fs/read?teamId=%s" % (sidB, TEAM), {"path": "/tmp/marker.txt"}, 20)
        log('restored B marker -> %s | %s' % (c, (r[:150] if r else '').replace(chr(10), ' ')))
        api("DELETE", "/v2/sandboxes/n17b?teamId=%s&projectId=%s" % (TEAM, PROJ))

# 6) 清理
api("DELETE", "/v2/sandboxes/n17a?teamId=%s&projectId=%s" % (TEAM, PROJ))
if snapA:
    api("DELETE", "/v2/sandboxes/snapshots/%s?project=%s" % (snapA, PROJ))
log('DONE')

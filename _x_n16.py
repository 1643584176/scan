# -*- coding: utf-8 -*-
"""非传统面A: 状态机/生命周期中间态 — stopping/snapshotting/resuming/deleting 窗口的 API 行为
重点: stopped 沙箱的 interactive/network-policy/cmd/fs 行为差异"""
import json, sys, time
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, TEAM, PROJ

def log(s): print(s, flush=True)

api("DELETE", "/v2/sandboxes/n16?teamId=%s&projectId=%s" % (TEAM, PROJ))
time.sleep(2)
c, r = api("POST", "/v4/sandboxes?teamId=%s" % TEAM, {"projectId": PROJ, "name": "n16"}, 60)
if c != 200:
    log('create fail %s' % r[:200]); sys.exit(1)
d = json.loads(r)['sandbox']
sid = d['currentSessionId']
log('n16 sid=%s status=%s' % (sid, d.get('status')))

def probe(tag):
    c, r = api("GET", "/v2/sandboxes/n16?teamId=%s&projectId=%s" % (TEAM, PROJ), None, 15)
    st = '?'
    if c == 200:
        try: st = json.loads(r).get('sandbox', {}).get('status')
        except Exception: pass
    log('[%s] GET status=%s (%s)' % (tag, st, c))

# 1) 创建后立即 (就绪窗口)
log('')
log('===== 1) 创建后就绪窗口 =====')
c, r = api("POST", "/v2/sandboxes/sessions/%s/cmd?teamId=%s" % (sid, TEAM),
           {"command": "id", "args": [], "wait": True, "timeout": 8000}, 20)
log('cmd-immediate -> %s | %s' % (c, (r[:120] if r else '').replace(chr(10), ' ')))

# 2) stop 中间态
log('')
log('===== 2) stop 中间态 =====')
c, r = api("POST", "/v2/sandboxes/sessions/%s/stop?teamId=%s" % (sid, TEAM), {}, 25)
log('stop -> %s | %s' % (c, (r[:200] if r else '').replace(chr(10), ' ')))
probe('after-stop-call')
# stopping 窗口内 cmd/interactive
c, r = api("POST", "/v2/sandboxes/sessions/%s/cmd?teamId=%s" % (sid, TEAM),
           {"command": "id", "args": [], "wait": True, "timeout": 6000}, 20)
log('cmd-during-stop -> %s | %s' % (c, (r[:120] if r else '').replace(chr(10), ' ')))
c, r = api("POST", "/v2/sandboxes/sessions/%s/interactive?teamId=%s" % (sid, TEAM), {}, 15)
log('interactive-during-stop -> %s | %s' % (c, (r[:160] if r else '').replace(chr(10), ' ')))
time.sleep(4)
probe('after-stop-settled')

# 3) stopped 状态全端点
log('')
log('===== 3) stopped 状态 =====')
c, r = api("POST", "/v2/sandboxes/sessions/%s/cmd?teamId=%s" % (sid, TEAM),
           {"command": "id", "args": [], "wait": True, "timeout": 6000}, 20)
log('cmd-stopped -> %s | %s' % (c, (r[:120] if r else '').replace(chr(10), ' ')))
c, r = api("POST", "/v2/sandboxes/sessions/%s/interactive?teamId=%s" % (sid, TEAM), {}, 15)
log('interactive-stopped -> %s | %s' % (c, (r[:200] if r else '').replace(chr(10), ' ')))
c, r = api("POST", "/v2/sandboxes/sessions/%s/network-policy?teamId=%s" % (sid, TEAM),
           {"mode": "deny-all"}, 15)
log('network-policy-stopped -> %s | %s' % (c, (r[:120] if r else '').replace(chr(10), ' ')))
c, r = api("POST", "/v2/sandboxes/sessions/%s/fs/read?teamId=%s" % (sid, TEAM), {"path": "/etc/passwd"}, 15)
log('fs-stopped -> %s | %s' % (c, (r[:120] if r else '').replace(chr(10), ' ')))
c, r = api("POST", "/v2/sandboxes/sessions/%s/extend-timeout?teamId=%s" % (sid, TEAM), {"duration": 60000}, 15)
log('extend-stopped -> %s | %s' % (c, (r[:120] if r else '').replace(chr(10), ' ')))
c, r = api("POST", "/v2/sandboxes/sessions/%s/snapshot?teamId=%s" % (sid, TEAM), {}, 15)
log('snapshot-stopped -> %s | %s' % (c, (r[:160] if r else '').replace(chr(10), ' ')))

# 4) stop 已 stop 沙箱
log('')
log('===== 4) 重复 stop =====')
c, r = api("POST", "/v2/sandboxes/sessions/%s/stop?teamId=%s" % (sid, TEAM), {}, 15)
log('stop-again -> %s | %s' % (c, (r[:120] if r else '').replace(chr(10), ' ')))

# 5) resume 中间态
log('')
log('===== 5) resume 中间态 =====')
c, r = api("GET", "/v2/sandboxes/n16?teamId=%s&projectId=%s&resume=true" % (TEAM, PROJ), None, 30)
log('resume -> %s' % c)
nsid = None
if c == 200:
    try:
        nsid = json.loads(r).get('sandbox', {}).get('currentSessionId')
        log('resume sid: %s' % nsid)
    except Exception: pass
# resuming 窗口立即 cmd (可能仍用旧 sid)
c, r = api("POST", "/v2/sandboxes/sessions/%s/cmd?teamId=%s" % (sid, TEAM),
           {"command": "id", "args": [], "wait": True, "timeout": 6000}, 20)
log('cmd-old-sid-during-resume -> %s | %s' % (c, (r[:120] if r else '').replace(chr(10), ' ')))
time.sleep(4)
if nsid:
    c, r = api("POST", "/v2/sandboxes/sessions/%s/cmd?teamId=%s" % (nsid, TEAM),
               {"command": "id", "args": [], "wait": True, "timeout": 8000}, 20)
    log('cmd-new-sid -> %s | %s' % (c, (r[:120] if r else '').replace(chr(10), ' ')))

api("DELETE", "/v2/sandboxes/n16?teamId=%s&projectId=%s" % (TEAM, PROJ))
log('DONE')

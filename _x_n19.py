# -*- coding: utf-8 -*-
"""非传统面D: source git 凭据回显 — 服务端 git clone 错误信息是否泄露 URL 中的 username/password"""
import json, sys, time
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, TEAM, PROJ

def log(s): print(s, flush=True)

# 1) gitUrl 带假凭据 + 不存在的仓库 → 错误信息回显?
api("DELETE", "/v2/sandboxes/n19?teamId=%s&projectId=%s" % (TEAM, PROJ))
time.sleep(2)
for tag, src in [
    ('cred-badhost', {"type": "git", "gitUrl": "https://secuser:S3cr3tPa55w0rd@badhost.invalid/repo.git", "revision": "main"}),
    ('cred-404repo', {"type": "git", "gitUrl": "https://secuser2:S3cr3tPa55w0rd2@github.com/vercel/this-repo-does-not-exist-xyz.git", "revision": "main"}),
    ('ssh-prefix', {"type": "git", "gitUrl": "ssh://git@ssh.github.com:443/vercel/vercel.git", "revision": "main"}),
]:
    c, r = api("POST", "/v4/sandboxes?teamId=%s" % TEAM,
               {"projectId": PROJ, "name": "n19-%s" % tag, "source": src}, 90)
    log('[%s] -> %s | %s' % (tag, c, (r[:300] if r else '').replace(chr(10), ' ')))
    if c == 200:
        try:
            name = json.loads(r)['sandbox']['name']
            api("DELETE", "/v2/sandboxes/%s?teamId=%s&projectId=%s" % (name, TEAM, PROJ))
        except Exception: pass
    time.sleep(1)

# 2) 快照列表元数据 (确认快照保留时列表可见性)
c, r = api("GET", "/v2/sandboxes/snapshots?project=%s" % PROJ, None, 20)
log('snapshots list -> %s | %s' % (c, (r[:300] if r else '').replace(chr(10), ' ')))
log('DONE')

# -*- coding: utf-8 -*-
"""非传统面D2: source git 凭据回显 — 正确字段名 url/username/password, 错误信息是否泄露凭据"""
import json, sys, time
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, TEAM, PROJ

def log(s): print(s, flush=True)

tests = [
    ('cred-fields', {"type": "git", "url": "https://github.com/vercel/does-not-exist-xyz.git",
                     "username": "secuser", "password": "S3cr3tPa55w0rd", "revision": "main"}),
    ('cred-in-url', {"type": "git", "url": "https://secuser2:S3cr3tPa55w0rd2@github.com/vercel/does-not-exist-xyz.git"}),
    ('ssh-url', {"type": "git", "url": "ssh://git@ssh.github.com:443/vercel/vercel.git"}),
    ('file-url', {"type": "git", "url": "file:///etc/passwd"}),
    ('badhost', {"type": "git", "url": "https://u:S3cr3t@badhost.invalid/repo.git"}),
]
for tag, src in tests:
    nm = "n19d-%s" % tag
    api("DELETE", "/v2/sandboxes/%s?teamId=%s&projectId=%s" % (nm, TEAM, PROJ))
    time.sleep(1)
    c, r = api("POST", "/v4/sandboxes?teamId=%s" % TEAM,
               {"projectId": PROJ, "name": nm, "source": src}, 90)
    body = (r or '')[:400].replace(chr(10), ' ')
    leak = 'S3cr3t' in body or 'secuser' in body or 'etc/passwd' in body
    log('[%s] -> %s%s | %s' % (tag, c, '  <<<LEAK!' if leak else '', body))
    if c == 200:
        try:
            name = json.loads(r)['sandbox']['name']
            api("DELETE", "/v2/sandboxes/%s?teamId=%s&projectId=%s" % (name, TEAM, PROJ))
        except Exception: pass
    time.sleep(1)
log('DONE')

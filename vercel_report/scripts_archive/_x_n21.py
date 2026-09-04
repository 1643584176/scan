# -*- coding: utf-8 -*-
"""非传统面E2: ①sudo 输出确认 ②fs/write Content-Type 矩阵 (CLI copy 上传格式)"""
import json, sys, time
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, TEAM, PROJ

def log(s): print(s, flush=True)

api("DELETE", "/v2/sandboxes/n21?teamId=%s&projectId=%s" % (TEAM, PROJ))
time.sleep(2)
c, r = api("POST", "/v4/sandboxes?teamId=%s" % TEAM, {"projectId": PROJ, "name": "n21"}, 60)
sid = json.loads(r)['sandbox']['currentSessionId']
log('sid=%s' % sid)
time.sleep(3)

# ① sudo: id -u + whoami + 敏感读
log('===== ① sudo 输出 =====')
c, r = api("POST", "/v2/sandboxes/sessions/%s/cmd?teamId=%s" % (sid, TEAM),
           {"command": "sh", "args": ["-c", "id -u; whoami; cat /proc/self/cgroup 2>/dev/null | head -3"],
            "wait": True, "timeout": 8000, "sudo": True}, 25)
log('sudo shell: %s | %s' % (c, (r or '').replace(chr(10), ' ')))
time.sleep(1)
# 非 sudo 对照
c, r = api("POST", "/v2/sandboxes/sessions/%s/cmd?teamId=%s" % (sid, TEAM),
           {"command": "sh", "args": ["-c", "id -u; whoami"], "wait": True, "timeout": 8000}, 25)
log('non-sudo: %s | %s' % (c, (r or '').replace(chr(10), ' ')))

# ② fs/write content-type 矩阵
log('')
log('===== ② fs/write CT 矩阵 =====')
import requests
BASE = 'https://api.vercel.com'
TOKEN = open(r'F:\scan\skills\non-traditional-vuln-hunting\vercel_driver.py', encoding='utf-8').read()
import re
m = re.search(r'TOKEN\s*=\s*["\']([^"\']+)', TOKEN)
tok = m.group(1)
hdr = {'Authorization': 'Bearer %s' % tok}
for tag, ct, body in [
    ('json', 'application/json', json.dumps({"path": "/tmp/ct_test.txt", "content": "CT1"})),
    ('text', 'text/plain', 'CT2'),
    ('octet', 'application/octet-stream', b'CT3'),
    ('form', 'application/x-www-form-urlencoded', 'path=/tmp/ct_test.txt&content=CT4'),
]:
    try:
        rr = requests.post('%s/v2/sandboxes/sessions/%s/fs/write?teamId=%s' % (BASE, sid, TEAM),
                           headers=dict(hdr, **{'Content-Type': ct}), data=body, timeout=20)
        log('[%s] -> %s | %s' % (tag, rr.status_code, rr.text[:200].replace(chr(10), ' ')))
    except Exception as e:
        log('[%s] err %s' % (tag, e))
# multipart (CLI 常见)
try:
    rr = requests.post('%s/v2/sandboxes/sessions/%s/fs/write?teamId=%s' % (BASE, sid, TEAM),
                       headers=hdr, files={'file': ('test.txt', b'CLI_COPY_MP_2026', 'text/plain')},
                       data={'path': '/tmp/mp_test.txt'}, timeout=20)
    log('[multipart] -> %s | %s' % (rr.status_code, rr.text[:200].replace(chr(10), ' ')))
except Exception as e:
    log('[multipart] err %s' % e)

# 读回验证
c, r = api("POST", "/v2/sandboxes/sessions/%s/fs/read?teamId=%s" % (sid, TEAM), {"path": "/tmp/ct_test.txt"}, 20)
log('read ct_test -> %s | %s' % (c, (r or '')[:150].replace(chr(10), ' ')))
c, r = api("POST", "/v2/sandboxes/sessions/%s/fs/read?teamId=%s" % (sid, TEAM), {"path": "/tmp/mp_test.txt"}, 20)
log('read mp_test -> %s | %s' % (c, (r or '')[:150].replace(chr(10), ' ')))

api("DELETE", "/v2/sandboxes/n21?teamId=%s&projectId=%s" % (TEAM, PROJ))
log('DONE')

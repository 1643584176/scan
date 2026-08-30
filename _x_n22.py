# -*- coding: utf-8 -*-
"""非传统面E3: ①sudo + logs:True 确认 root ②fs/write CT 矩阵 (用 driver TOKEN)"""
import json, sys, time, requests, urllib.request, urllib.error
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, TOKEN, TEAM, PROJ, BASE

def log(s): print(s, flush=True)

api("DELETE", "/v2/sandboxes/n22?teamId=%s&projectId=%s" % (TEAM, PROJ))
time.sleep(2)
c, r = api("POST", "/v4/sandboxes?teamId=%s" % TEAM, {"projectId": PROJ, "name": "n22"}, 60)
sid = json.loads(r)['sandbox']['currentSessionId']
log('sid=%s' % sid)
time.sleep(3)

# ① sudo + logs
log('===== ① sudo + logs =====')
for tag, body in [
    ('sudo', {"command": "sh", "args": ["-c", "id -u; whoami; cat /etc/hostname; ls -la / | head -15"],
              "wait": True, "timeout": 10000, "logs": True, "sudo": True}),
    ('nosudo', {"command": "sh", "args": ["-c", "id -u; whoami; ls -la / | head -5"],
                "wait": True, "timeout": 10000, "logs": True}),
]:
    c, r = api("POST", "/v2/sandboxes/sessions/%s/cmd?teamId=%s" % (sid, TEAM), body, 30)
    log('[%s] -> %s | %s' % (tag, c, (r or '').replace(chr(10), ' ')))

# ② fs/write CT 矩阵
log('')
log('===== ② fs/write CT 矩阵 =====')
hdr = {'Authorization': 'Bearer %s' % TOKEN}
for tag, ct, body in [
    ('json', 'application/json', json.dumps({"path": "/tmp/ct_test.txt", "content": "CT1"})),
    ('text', 'text/plain', 'CT2'),
    ('form', 'application/x-www-form-urlencoded', 'path=/tmp/ct_test.txt&content=CT4'),
]:
    try:
        rr = requests.post('%s/v2/sandboxes/sessions/%s/fs/write?teamId=%s' % (BASE, sid, TEAM),
                           headers=dict(hdr, **{'Content-Type': ct}), data=body, timeout=20)
        log('[%s] -> %s | %s' % (tag, rr.status_code, rr.text[:250].replace(chr(10), ' ')))
    except Exception as e:
        log('[%s] err %s' % (tag, e))
try:
    rr = requests.post('%s/v2/sandboxes/sessions/%s/fs/write?teamId=%s' % (BASE, sid, TEAM),
                       headers=hdr, files={'file': ('test.txt', b'CLI_COPY_MP_2026', 'text/plain')},
                       data={'path': '/tmp/mp_test.txt'}, timeout=20)
    log('[multipart] -> %s | %s' % (rr.status_code, rr.text[:250].replace(chr(10), ' ')))
except Exception as e:
    log('[multipart] err %s' % e)
# 读回验证
c, r = api("POST", "/v2/sandboxes/sessions/%s/fs/read?teamId=%s" % (sid, TEAM), {"path": "/tmp/ct_test.txt"}, 20)
log('read ct_test -> %s | %s' % (c, (r or '')[:150].replace(chr(10), ' ')))
c, r = api("POST", "/v2/sandboxes/sessions/%s/fs/read?teamId=%s" % (sid, TEAM), {"path": "/tmp/mp_test.txt"}, 20)
log('read mp_test -> %s | %s' % (c, (r or '')[:150].replace(chr(10), ' ')))

api("DELETE", "/v2/sandboxes/n22?teamId=%s&projectId=%s" % (TEAM, PROJ))
log('DONE')

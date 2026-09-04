# -*- coding: utf-8 -*-
"""Guest 面深入 4: sandbox-init strings 宽泛侦察 + sudo/用户面
K1: id / sudo 可用性 (mount 失败原因)
K2: strings 头 80 行 (内容类型)
K3: strings 宽泛 grep (vercel|go1|cell|api|http|snapshot|socket)
K4: sandbox-init 权限位 (setuid?) + 可执行性 (运行 --help?)
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

def run(tag, sc, maxlen=1100):
    c, r = cmd(sid, 'sh', ['-c', sc], timeout_ms=60000)
    out = ''
    for line in r.splitlines():
        if '"data"' in line:
            try:
                out += json.loads(line).get('data', '')
            except Exception:
                pass
    print('[%s] %s' % (tag, out[:maxlen]), flush=True)
    return out

# K1: 用户面
run('K1-user', 'id; echo ===; sudo -n id 2>&1; echo ===; which sudo su mount strings 2>&1')

# K2: strings 头
run('K2-strings-head', 'strings /run/vercel/share/sandbox-init 2>&1 | head -60')

# K3: 宽泛 grep
run('K3-strings-grep', 'strings /run/vercel/share/sandbox-init 2>&1 | grep -iE "vercel|go1|cell|snapshot|socket|v2/|/v1/|:443|:80|api" | head -40')

# K4: 权限/执行
run('K4-exec', 'ls -la /run/vercel/share/sandbox-init; /run/vercel/share/sandbox-init --help 2>&1 | head -10; echo RC=$?')

print('=== G5 DONE ===', flush=True)

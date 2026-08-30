# -*- coding: utf-8 -*-
"""Guest 面深入 5: sandbox-init 逆向 (python strings) + mount vda + 运行观察
K5: python strings 提取关键词 (grpc/api/socket/host 地址)
K6: sudo mount vda 只读 -> ls (known 面确认)
K7: 运行 sandbox-init (假 pubkey) 观察行为/连接目标
"""
import base64, json, sys, time
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

def run(tag, sc, maxlen=1400):
    c, r = cmd(sid, 'sh', ['-c', sc], timeout_ms=90000)
    out = ''
    for line in r.splitlines():
        if '"data"' in line:
            try:
                out += json.loads(line).get('data', '')
            except Exception:
                pass
    print('[%s] %s' % (tag, out[:maxlen]), flush=True)
    return out

STR_CODE = '''import re
data = open('/run/vercel/share/sandbox-init','rb').read()
strs = re.findall(rb'[\\x20-\\x7e]{8,}', data)
kw = [b'vercel', b'grpc', b'/v1', b'/v2', b'/v3', b'api', b'cell', b'snapshot', b'token', b'secret',
      b'http', b'443', b'169.254', b'100.64', b'172.16', b'192.168', b'10.0', b'10.1', b'10.2',
      b'kube', b'containerd', b'base_url', b'metadata', b'aws', b'iam', b'listen', b'bind',
      b'credential', b'authorization', b'pubkey', b'ed25519', b'gopls', b'/home/', b'/root', b'/tmp/']
seen = set()
n = 0
for s in strs:
    low = s.lower()
    if any(k in low for k in kw):
        t = s.decode('utf-8', 'replace')
        if t not in seen and n < 120:
            seen.add(t)
            print(t)
            n += 1
print('TOTAL_MATCH', n)
'''

# K5: python strings
b64 = base64.b64encode(STR_CODE.encode()).decode()
run('K5-strings', 'echo %s | base64 -d | python3' % b64, maxlen=1600)

# K6: sudo mount vda
run('K6-vda', 'sudo mkdir -p /mnt/vda; sudo mount -o ro /dev/vda /mnt/vda 2>&1; echo ===; sudo ls -la /mnt/vda/ 2>&1 | head -30')

# K7: 运行 sandbox-init (假 pubkey, 观察)
run('K7-run', 'echo AAA= | base64 -d 2>/dev/null; sudo /run/vercel/share/sandbox-init -socket /tmp/me.sock -pubkey AAA= 2>&1 & sleep 3; ls -la /tmp/me.sock 2>&1; sudo cat /proc/net/unix 2>/dev/null | head -5; sudo ls /proc/ 2>/dev/null | grep -c . >/dev/null; ps aux 2>&1 | grep -i sandbox | head -3; pkill -f sandbox-init 2>/dev/null; echo K7_DONE')

print('=== G6 DONE ===', flush=True)

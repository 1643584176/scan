# -*- coding: utf-8 -*-
"""重建沙箱 -> 拷贝 sandbox-init -> 注入分析脚本 -> 运行
记录 pubkey, 对比是否每沙箱不同"""
import base64, sys, time
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import cmd, fresh_sandbox

ANALYZER = r'''
import re
data = open('/vercel/sandbox/init.bin','rb').read()
print('size', len(data))
print('head', data[:4].hex())
i = data.find(b'\xff Go buildinfo:')
print('go buildinfo offset', i)
strs = re.findall(rb'[\x20-\x7e]{6,}', data)
seen = set()
def has(kw, limit=20):
    out = []
    for s in strs:
        if kw.encode() in s.lower():
            t = s.decode(errors='replace')
            if t not in seen:
                seen.add(t)
                out.append(t)
        if len(out) >= limit:
            break
    return out
for kw in ['spawn', 'signature', 'pubkey', 'ed25519', 'vercel.sandbox', 'connect', 'timestamp', 'grpc']:
    print('--- %s ---' % kw)
    print(has(kw))
'''

sid = fresh_sandbox("exp_init")
print("sid:", sid)
time.sleep(2)

c, r = cmd(sid, "bash", ["-c", "cp /run/vercel/share/sandbox-init /vercel/sandbox/init.bin 2>&1; cat /proc/1/cmdline | tr '\\0' ' '; echo; ls -la /vercel/sandbox/init.bin"], timeout_ms=30000)
print("cp+cmdline:", c, r[:600])

payload = base64.b64encode(ANALYZER.encode()).decode()
inject = "import base64;open('/vercel/sandbox/analyze.py','wb').write(base64.b64decode('%s'))" % payload
c, r = cmd(sid, "python3", ["-c", inject], timeout_ms=30000)
print("inject:", c, r[:150])

c, r = cmd(sid, "python3", ["/vercel/sandbox/analyze.py"], timeout_ms=120000)
print("=== analyze ===")
print(r[:5000])

# -*- coding: utf-8 -*-
"""沙箱内 python 提取 init.bin 字符串(base64 注入, 避免引号转义)"""
import base64, sys
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import cmd

SID = "sbx_PcSQVxXAgAuH9friOUhAFMWvlmr4"

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
for kw in ['spawn', 'signature', 'pubkey', 'ed25519', 'vercel.sandbox', 'connect', 'timestamp']:
    print('--- %s ---' % kw)
    print(has(kw))
'''

payload = base64.b64encode(ANALYZER.encode()).decode()
inject = "import base64;open('/vercel/sandbox/analyze.py','wb').write(base64.b64decode('%s'))" % payload
c, r = cmd(SID, "python3", ["-c", inject], timeout_ms=30000)
print("inject:", c, r[:150])
c, r = cmd(SID, "python3", ["/vercel/sandbox/analyze.py"], timeout_ms=90000)
print("=== analyze ===")
print(r[:4000])

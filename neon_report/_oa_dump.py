# -*- coding: utf-8 -*-
"""dump Neon v2 全部 operationId -> 人工浏览清单"""
import json

spec = json.load(open(r'D:\scan\neon_report\_openapi_v2.json', encoding='utf-8'))
paths = spec.get('paths', {})

out = []
for p in sorted(paths):
    for m, o in paths[p].items():
        if not isinstance(o, dict) or 'operationId' not in o:
            continue
        tags = ','.join(o.get('tags', []))
        sec = o.get('security', [])
        seck = [list(s.keys())[0] for s in sec] if sec else ['NONE']
        summ = (o.get('summary') or '')[:90]
        out.append('%s %-6s [%-22s] sec=%-10s %s :: %s' % (p, m.upper(), tags, ','.join(seck), o['operationId'], summ))

lines = sorted(out)
open(r'D:\scan\neon_report\_oplist.txt', 'w', encoding='utf-8').write('\n'.join(lines))
print('total ops:', len(lines))
# 技术原语关键词高亮
KEY = ['presign', 'restore', 'clone', 'copy', 'rotate', 'import', 'export', 'migrat', 'share', 'token', 'credential',
       'key', 'password', 'reset', 'exec', 'sql', 'function', 'invoke', 'call', 'gateway', 'webhook', 'snapshot',
       'fork', 'transfer', 'role', 'sudo', 'admin', 'consume', 'storage', 'bucket', 'object', 'presigned', 'secret',
       'ssrf', 'proxy', 'redirect']
for ln in lines:
    if any(k.lower() in ln.lower() for k in KEY):
        print(ln)

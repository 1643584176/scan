# -*- coding: utf-8 -*-
"""查 organizations/projects list 的正确路径与参数"""
import json

d = json.load(open('D:/scan/neon_report/_openapi_v2.json', encoding='utf-8'))
paths = d.get('paths', {})

for p in sorted(paths):
    if p in ('/projects', '/organizations') or p.startswith('/organizations') or 'org' in p.lower() and p.count('/') <= 2:
        ops = paths[p]
        for m, op in ops.items():
            if not isinstance(op, dict):
                continue
            prms = []
            for prm in op.get('parameters', []):
                sch = prm.get('schema', {})
                prms.append('%s %s req=%s' % (prm.get('in'), prm.get('name'), prm.get('required', False)))
            print('%s %s | %s | params: %s' % (m.upper(), p, op.get('summary', '')[:60], ', '.join(prms)))

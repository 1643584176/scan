# -*- coding: utf-8 -*-
"""Enumerate DB/query-related endpoints from Box OpenAPI."""
import json
import sys

spec = json.load(open(r'F:/scan/box_report/box_openapi.json', encoding='utf-8'))
paths = spec.get('paths', {})
kw = ['search', 'metadata', 'query', 'ai', 'event', 'report', 'collaboration',
      'filter', 'sort', 'relay', 'form', 'note', 'task', 'comment', 'shared',
      'shield', 'governance', 'retention', 'classification', 'watermark',
      'sign', 'workflow', 'weblink', 'group', 'user', 'enterprise', 'device']
out = []
for p, methods in paths.items():
    for m, op in methods.items():
        if m not in ('get', 'post', 'put', 'delete', 'options', 'patch'):
            continue
        low = p.lower()
        summ = (op.get('summary') or '')[:120]
        tag = (op.get('tags') or [''])[0]
        if any(k in low for k in kw):
            params = []
            for prm in op.get('parameters', []):
                params.append(prm.get('name'))
            out.append('%s %-6s %-70s | %s | %s' % (tag[:18], m.upper(), p, summ, ','.join(params[:8])))
out.sort()
sys.stdout.write('\n'.join(out))
sys.stdout.write('\nTOTAL: %d\n' % len(out))

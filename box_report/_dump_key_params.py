# -*- coding: utf-8 -*-
"""Dump detailed params for key query-surface endpoints."""
import json
import sys

spec = json.load(open(r'F:/scan/box_report/box_openapi.json', encoding='utf-8'))
paths = spec.get('paths', {})
want = [
    '/search', '/metadata_queries/execute_read', '/users',
    '/groups', '/retention_policies', '/metadata_taxonomies/{namespace}/{taxonomy_key}/nodes',
    '/metadata_templates/{namespace}/{template_key}/fields/{field_key}/options',
    '/events', '/ai/ask', '/workflows', '/file_version_retentions',
]
for p in want:
    if p not in paths:
        sys.stdout.write('### %s NOT FOUND\n\n' % p)
        continue
    sys.stdout.write('### %s\n' % p)
    for m, op in paths[p].items():
        if m not in ('get', 'post'):
            continue
        sys.stdout.write('  %s: %s\n' % (m.upper(), (op.get('summary') or '')[:100]))
        for prm in op.get('parameters', []):
            sch = prm.get('schema', {})
            sys.stdout.write('    - %s (%s): %s  example=%s\n' % (
                prm.get('name'), sch.get('type') or sch.get('format') or 'obj',
                (prm.get('description') or '')[:180].replace('\n', ' '),
                json.dumps(sch.get('example', ''), ensure_ascii=False)[:100]))
        rb = op.get('requestBody', {})
        if rb:
            content = rb.get('content', {})
            for ct, cval in content.items():
                sch = cval.get('schema', {})
                props = sch.get('properties', {})
                sys.stdout.write('    BODY[%s]: required=%s\n' % (ct, sch.get('required')))
                for pn, pv in props.items():
                    sys.stdout.write('        .%s: %s | %s\n' % (
                        pn, pv.get('type') or pv.get('$ref', '').split('/')[-1],
                        (pv.get('description') or '')[:150].replace('\n', ' ')))
    sys.stdout.write('\n')

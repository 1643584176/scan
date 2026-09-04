# -*- coding: utf-8 -*-
"""列出 OpenAPI 中所有 auth 相关路径及方法"""
import json
d = json.load(open('_openapi_v2.json', encoding='utf-8'))
for p, v in d['paths'].items():
    if 'auth' in p.lower():
        methods = [m.upper() for m in v.keys() if m in ('get', 'post', 'put', 'patch', 'delete', 'head', 'options')]
        # 取第一个 summary
        tags = set()
        for m in methods:
            op = v.get(m.lower(), {})
            for t in op.get('tags', []):
                tags.add(t)
        print('%-75s %-28s %s' % (p, ','.join(methods), ','.join(sorted(tags))))

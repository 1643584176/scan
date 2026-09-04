# -*- coding: utf-8 -*-
"""查看 swagger.yml 中 database 相关 path 的定义"""
import yaml

spec = yaml.safe_load(open(r'D:\scan\netlify_report\_openapi\swagger.yml', encoding='utf-8'))
for p, ops in spec['paths'].items():
    if 'database' in p:
        print('PATH:', p)
        print('  methods:', list(ops.keys()))
        for m, op in ops.items():
            if m in ('get', 'post', 'delete', 'put', 'patch'):
                print('   %s: %s' % (m.upper(), op.get('summary', '')))
                for prm in op.get('parameters', []):
                    print('      param:', prm.get('name'), prm.get('in'), 'req=%s' % prm.get('required'))
                # requestBody schema 字段名
                rb = op.get('requestBody', {})
                if rb:
                    content = rb.get('content', {})
                    for ct, cdef in content.items():
                        sch = cdef.get('schema', {})
                        props = list(sch.get('properties', {}).keys())
                        print('      body[%s] props:' % ct, props)
        print()

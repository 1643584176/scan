# -*- coding: utf-8 -*-
"""提取 SslEnforcementRequest/JitAccess* 相关 components schema 定义"""
import json, os

d = os.path.dirname(os.path.abspath(__file__))
spec = json.load(open(os.path.join(d, '_sb16_openapi.json'), encoding='utf-8'))
sch = spec.get('components', {}).get('schemas', {})

out = []
for name in sorted(sch):
    if ('jit' in name.lower() or 'ssl' in name.lower()) and ('request' in name.lower() or 'response' in name.lower() or 'config' in name.lower() or name.lower().startswith('jit') or name.lower().startswith('ssl')):
        out.append('### %s' % name)
        out.append(json.dumps(sch[name], ensure_ascii=False, indent=1))
open(os.path.join(d, '_sb32d_spec_schemas.txt'), 'w', encoding='utf-8').write('\n'.join(out))
print('\n'.join(out))

# -*- coding: utf-8 -*-
"""提取 /database/jit/invite + invite/accept + list 的完整 OpenAPI 定义"""
import json, os

d = os.path.dirname(os.path.abspath(__file__))
spec = json.load(open(os.path.join(d, '_sb16_openapi.json'), encoding='utf-8'))

out = []
for p in sorted(spec['paths']):
    if 'jit/invite' in p or 'jit/list' in p:
        out.append('### %s' % p)
        out.append(json.dumps(spec['paths'][p], ensure_ascii=False, indent=1))

# 相关 schema
sch = spec.get('components', {}).get('schemas', {})
for n in ['InviteExternalUserJitAccessBody', 'AcceptInviteExternalUserJitAccessBody', 'JitListAccessResponse_Output']:
    if n in sch:
        out.append('### SCHEMA %s' % n)
        out.append(json.dumps(sch[n], ensure_ascii=False, indent=1))
open(os.path.join(d, '_sb48_invite_spec.txt'), 'w', encoding='utf-8').write('\n'.join(out))
print('\n'.join(out))

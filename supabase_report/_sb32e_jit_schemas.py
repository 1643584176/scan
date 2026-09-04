# -*- coding: utf-8 -*-
"""提取 JIT 相关全部 components schema 定义"""
import json, os

d = os.path.dirname(os.path.abspath(__file__))
spec = json.load(open(os.path.join(d, '_sb16_openapi.json'), encoding='utf-8'))
sch = spec.get('components', {}).get('schemas', {})

names = ['AuthorizeJitAccessBody', 'UpdateJitAccessBody', 'JitAccessResponse_Output',
         'JitAuthorizeAccessResponse_Output', 'JitInviteExternalUserBody',
         'AcceptExternalUserJitBody', 'InviteExternalUserJitResponse_Output',
         'JitAccessJitRole', 'JitRole', 'JitAccessAllowedNetworks', 'UserRoleMapping']
out = []
for name in names:
    if name in sch:
        out.append('### %s' % name)
        out.append(json.dumps(sch[name], ensure_ascii=False, indent=1))
    else:
        out.append('### %s (NOT FOUND)' % name)
# 列出所有含 Jit 的 schema 名
out.append('--- all Jit schemas ---')
out.append(', '.join(sorted(n for n in sch if 'Jit' in n or 'jit' in n)))
open(os.path.join(d, '_sb32e_jit_schemas.txt'), 'w', encoding='utf-8').write('\n'.join(out))
print('\n'.join(out))

# -*- coding: utf-8 -*-
"""公开侦察19: *_Output schemas 展开 (JIT/claim/login-role/snippets 响应结构)"""
import os, json

here = os.path.dirname(os.path.abspath(__file__))
spec = json.load(open(os.path.join(here, '_sb16_openapi.json'), encoding='utf-8'))
comp = spec.get('components', {}).get('schemas', {})

want = ['JitAccessResponse_Output', 'JitAuthorizeAccessResponse_Output', 'JitListAccessResponse_Output',
        'InviteExternalUserJitResponse_Output', 'ProjectClaimTokenResponse_Output',
        'CreateProjectClaimTokenResponse_Output', 'OrganizationProjectClaimResponse_Output',
        'CreateRoleResponse_Output', 'DeleteRolesResponse_Output', 'SnippetResponse_Output',
        'SnippetList_Output', 'ReadOnlyStatusResponse_Output', 'GetProjectDbMetadataResponse_Output',
        'UpdateJitAccessBody', 'AuthorizeJitAccessBody', 'InviteExternalUserJitAccessBody',
        'CreateProjectClaimTokenBody', 'ProjectClaimToken']
out = []
for nm in want:
    if nm not in comp:
        out.append('### %s NOT FOUND' % nm)
        continue
    out.append('#' * 70)
    out.append('SCHEMA %s' % nm)
    out.append(json.dumps(comp[nm], indent=1, ensure_ascii=False)[:3000])
open(os.path.join(here, '_sb19_output_schemas.txt'), 'w', encoding='utf-8').write('\n'.join(out))
print('lines:', len(out))

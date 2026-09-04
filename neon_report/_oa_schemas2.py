# -*- coding: utf-8 -*-
"""补:枚举 + Auth 面 schema 细节"""
import json

spec = json.load(open(r'D:\scan\neon_report\_openapi_v2.json', encoding='utf-8'))
comps = spec['components']['schemas']

WANT = ['CredentialScope', 'GrantedCredentialScope', 'NeonAuthSupportedAuthProvider',
        'NeonAuthWebhookConfig', 'UpdateNeonAuthUserRoleRequest', 'CreateBranchNeonAuthNewUserRequest',
        'Bucket', 'DataAPICreateResponse', 'NeonFunction', 'CustomDomain', 'DataAPISettings',
        'BackupSchedule', 'SnapshotUpdateRequest', 'TransferProjectsToOrganizationRequest',
        'NeonAuthTransferAuthProviderProjectRequest', 'CreateCredentialRequest']
for n in WANT:
    s = comps.get(n, {})
    print('\n== %s: type=%s' % (n, s.get('type')))
    if s.get('enum'):
        print('  ENUM:', s['enum'])
    if s.get('type') == 'array':
        it = s.get('items', {})
        print('  items:', it.get('enum') or it.get('$ref'))
    for pn, pv in (s.get('properties') or {}).items():
        req = 'REQ' if pn in s.get('required', []) else 'opt'
        if '$ref' in pv:
            rn = pv['$ref'].split('/')[-1]
            rs = comps.get(rn, {})
            print('  - %s (%s) -> %s %s %s' % (pn, req, rn, rs.get('type'), rs.get('enum')))
        else:
            print('  - %s (%s) %s %s %s' % (pn, req, pv.get('type'), pv.get('enum'), (pv.get('description') or '')[:120]))

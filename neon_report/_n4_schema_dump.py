# -*- coding: utf-8 -*-
"""dump functions/credentials/custom-domain 相关 schema 定义"""
import json
d = json.load(open(r'D:\scan\neon_report\_openapi_v2.json'))
s = d['components']['schemas']
targets = ['FunctionDeployRequest', 'NeonFunctionResponse', 'NeonFunctionsListResponse',
           'NeonFunctionDeploymentResponse', 'CustomDomain', 'CustomDomainRegisterRequest',
           'BranchCredentialCreateRequest', 'BranchCredential', 'NeonCredential',
           'CustomDomainsListResponse']
for t in targets:
    if t in s:
        print('=' * 20, t)
        print(json.dumps(s[t], indent=1)[:1600])
    else:
        print('=' * 20, t, 'NOT FOUND')

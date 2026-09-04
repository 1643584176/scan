# -*- coding: utf-8 -*-
"""invite 500 原因区分: 角色校验 vs 邮箱校验 vs 功能 gate"""
import http.client, ssl, json, time, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _supabase_creds import BEARER_JWT, VDP_HEADERS, UA, API_HOST, PROJECT_REF, EMAIL

# 0. 本地 spec 查 accept body schema
d = os.path.dirname(os.path.abspath(__file__))
spec = json.load(open(os.path.join(d, '_sb16_openapi.json'), encoding='utf-8'))
sch = spec.get('components', {}).get('schemas', {})
ab = sch.get('AcceptInviteExternalUserJitAccessBody')
print('### AcceptInviteExternalUserJitAccessBody')
print(json.dumps(ab, ensure_ascii=False, indent=1) if ab else 'NOT FOUND')
il = sch.get('JitListAccessResponse_Output')
print('### JitListAccessResponse_Output')
print(json.dumps(il, ensure_ascii=False, indent=1)[:1500] if il else 'NOT FOUND')

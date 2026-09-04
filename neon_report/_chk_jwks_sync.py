# -*- coding: utf-8 -*-
"""检查 JWKS 同步链路:neonauth host 端点 vs Data API"""
import http.client, ssl, json

ctx = ssl.create_default_context()
AUTH = 'ep-crimson-fog-w2gucld1.neonauth.us-east-2.aws.neon.build'

conn = http.client.HTTPSConnection(AUTH, context=ctx, timeout=15)
conn.request('GET', '/neondb/auth/.well-known/jwks.json', headers={'User-Agent': 'Mozilla/5.0'})
r = conn.getresponse(); raw = r.read().decode(errors='replace')
print('neonauth jwks status:', r.status)
data = json.loads(raw) if r.status == 200 else {}
keys = data.get('keys', [])
print('keys:', len(keys))
for k in keys:
    print('  kid=', k.get('kid'), 'kty=', k.get('kty'), 'crv=', k.get('crv'))
conn.close()

# Data API 匿名访问(不带 JWT)看错误是否还是强制 JWT
DA = 'ep-crimson-fog-w2gucld1.apirest.us-east-2.aws.neon.build'
conn = http.client.HTTPSConnection(DA, context=ctx, timeout=15)
conn.request('GET', '/neondb/rest/v1/', headers={'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json'})
r = conn.getresponse(); raw = r.read().decode(errors='replace')
print('\ndata-api root status:', r.status)
print(raw[:400])
conn.close()

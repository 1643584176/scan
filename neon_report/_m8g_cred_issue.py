# -*- coding: utf-8 -*-
"""Credential 签发 + AI Gateway 认证链验证(自己项目)
1. issue credential (storage:read + ai_gateway:invoke)
2. api_token 调自己 AI gateway models
3. reveal 行为确认"""
import http.client, ssl, json, time, os, sys

ctx = ssl.create_default_context()
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _neon_creds_stage import API_HOST, API_BASE
keyj = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '_apikey.json')))
KEY = keyj.get('key') or keyj.get('api_key') or keyj.get('token') or list(keyj.values())[0]
ctxj = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '_ctx.json')))
PID, BID = ctxj['pid'], ctxj['bid']
AI = 'br-wandering-field-w2ob6mpn-api.ai.c-1.us-east-2.aws.neon.build'

def req(host, method, path, body=None, headers=None):
    try:
        conn = http.client.HTTPSConnection(host, context=ctx, timeout=20)
        h = {'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json', 'Content-Type': 'application/json'}
        if headers:
            h.update(headers)
        conn.request(method, path, body=json.dumps(body).encode() if body is not None else None, headers=h)
        r = conn.getresponse()
        raw = r.read()
        st = r.status
        hdrs = dict((k.lower(), v) for k, v in r.getheaders())
        conn.close()
        return st, raw.decode('utf-8', 'replace'), hdrs
    except Exception as e:
        return -1, 'EXC %s' % e, {}

cb = {'Authorization': 'Bearer ' + str(KEY), 'X-Bug-Bounty': 'xxbo'}

print('=== [1] list 现有凭据 ===')
st, raw, _ = req(API_HOST, 'GET', API_BASE + '/projects/%s/branches/%s/credentials' % (PID, BID), headers=cb)
print('%d %s' % (st, raw[:400]))

print('\n=== [2] issue credential ===')
st, raw, _ = req(API_HOST, 'POST', API_BASE + '/projects/%s/branches/%s/credentials' % (PID, BID),
                 {'name': 'sec-test-m8g-%d' % (time.time() % 1000),
                  'scopes': ['storage:read', 'ai_gateway:invoke'], 'principal_type': 'user'}, headers=cb)
print('%d %s' % (st, raw[:600]))
try:
    cred = json.loads(raw)
    tok_id = cred.get('token_id', '')
    api_tok = cred.get('api_token', '')
    s3_secret = cred.get('s3_secret_access_key', '')
except Exception:
    tok_id = api_tok = s3_secret = ''
print('token_id 前20:', tok_id[:20], 'api_token 前12:', api_tok[:12], 's3_secret 前8:', s3_secret[:8])

if api_tok:
    print('\n=== [3] api_token 调 AI gateway models ===')
    for hdr_name, val in [('Authorization', 'Bearer ' + api_tok),
                          ('X-API-Key', api_tok),
                          ('Authorization', api_tok)]:
        st, raw, hdrs = req(AI, 'GET', '/ai-gateway/openai/v1/models', headers={hdr_name: val})
        print('[%s] -> %d %s' % (hdr_name, st, raw[:300]))
        if st == 200:
            print('  认证方式确认:', hdr_name)
            break
        time.sleep(0.3)

print('\n=== [4] reveal 行为 ===')
if tok_id:
    st, raw, _ = req(API_HOST, 'POST', API_BASE + '/projects/%s/branches/%s/credentials/%s/reveal' % (PID, BID, tok_id),
                     headers=cb)
    print('reveal -> %d %s' % (st, raw[:250]))

print('\n=== [5] cleanup: revoke ===')
if tok_id:
    st, raw, _ = req(API_HOST, 'DELETE', API_BASE + '/projects/%s/branches/%s/credentials/%s' % (PID, BID, tok_id),
                     headers=cb)
    print('revoke -> %d %s' % (st, raw[:120]))

# -*- coding: utf-8 -*-
"""AI Gateway 403 层判别: 无auth vs 有auth vs header 变体"""
import http.client, ssl, json, time, os, sys

ctx = ssl.create_default_context()
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _neon_creds_stage import API_HOST, API_BASE
keyj = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '_apikey.json')))
KEY = keyj.get('key') or keyj.get('api_key') or keyj.get('token') or list(keyj.values())[0]
ctxj = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '_ctx.json')))
PID, BID = ctxj['pid'], ctxj['bid']
AI = 'br-wandering-field-w2ob6mpn-api.ai.c-1.us-east-2.aws.neon.build'

def req(host, method, path, body=None, headers=None, show_hdrs=False):
    try:
        conn = http.client.HTTPSConnection(host, context=ctx, timeout=15)
        h = {'Content-Type': 'application/json'}
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
st, raw, _ = req(API_HOST, 'GET', API_BASE + '/projects/%s/branches/%s/credentials' % (PID, BID), headers=cb)
creds = json.loads(raw).get('credentials', [])
ai_tok = ''
for c in creds:
    if 'ai_gateway' in c.get('scopes', []):
        st, raw2, _ = req(API_HOST, 'POST', API_BASE + '/projects/%s/branches/%s/credentials/%s/reveal' % (PID, BID, c['token_id']), headers=cb)
        try:
            ai_tok = json.loads(raw2).get('api_token', '')
            print('用凭据:', c.get('name'), c['token_id'][:16])
            break
        except Exception:
            pass
    time.sleep(0.2)

print('\n=== 判别矩阵 (/v1/models) ===')
tests = [
    ('无 auth', {}),
    ('Bearer 正确', {'Authorization': 'Bearer ' + ai_tok}),
    ('Bearer 前缀小写', {'authorization': 'bearer ' + ai_tok}),
    ('Bearer 正确 + BB', {'Authorization': 'Bearer ' + ai_tok, 'X-Bug-Bounty': 'xxbo'}),
    ('openai UA', {'Authorization': 'Bearer ' + ai_tok, 'User-Agent': 'openai-python/1.55.3'}),
    ('无 UA', {'Authorization': 'Bearer ' + ai_tok, 'User-Agent': ''}),
    ('token 格式错', {'Authorization': 'Bearer nt_live_xxxx'}),
]
for tag, hdrs in tests:
    st, raw, hdrs_r = req(AI, 'GET', '/v1/models', headers=hdrs, show_hdrs=True)
    print('[%s] -> %d %s' % (tag, st, raw[:180]))
    time.sleep(0.2)

print('\n=== www 前缀/HTTP/其他 host 形态 ===')
for h2 in ('br-wandering-field-w2ob6mpn-api.ai.c-1.us-east-2.aws.neon.build',):
    pass
# 试 OPTIONS 看 CORS/允许头
st, raw, hdrs = req(AI, 'OPTIONS', '/v1/models', headers={'Origin': 'https://example.com', 'Access-Control-Request-Method': 'GET'})
print('[OPTIONS] -> %d %s' % (st, json.dumps(dict((k, v) for k, v in hdrs.items() if k.startswith('access-control') or k == 'allow') or raw[:100], ensure_ascii=False)))

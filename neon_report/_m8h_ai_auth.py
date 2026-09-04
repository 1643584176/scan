# -*- coding: utf-8 -*-
"""AI Gateway 认证调试: reveal 默认凭据 + 路径/方法矩阵"""
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
        conn.close()
        return st, raw.decode('utf-8', 'replace')
    except Exception as e:
        return -1, 'EXC %s' % e

cb = {'Authorization': 'Bearer ' + str(KEY), 'X-Bug-Bounty': 'xxbo'}

print('=== [1] list + reveal 默认凭据 ===')
st, raw = req(API_HOST, 'GET', API_BASE + '/projects/%s/branches/%s/credentials' % (PID, BID), headers=cb)
creds = json.loads(raw).get('credentials', [])
print('凭据数:', len(creds))
tokens = {}
for c in creds:
    tid = c['token_id']
    st, raw2 = req(API_HOST, 'POST', API_BASE + '/projects/%s/branches/%s/credentials/%s/reveal' % (PID, BID, tid),
                   headers=cb)
    try:
        j = json.loads(raw2)
        tokens[tid] = j.get('api_token', '')
        print('reveal %s (%s) scopes=%s -> api_token 前16=%s' % (c.get('name', '')[:36], tid[:16],
              c.get('scopes'), tokens[tid][:16]))
    except Exception:
        print('reveal %s -> %d %s' % (tid[:16], st, raw2[:150]))
    time.sleep(0.3)

# 用 AI 默认凭据测试
ai_tok = ''
for c in creds:
    if 'ai' in c.get('name', '').lower() or 'ai_gateway' in c.get('scopes', []):
        ai_tok = tokens.get(c['token_id'], '')
        break
if not ai_tok:
    ai_tok = list(tokens.values())[0] if tokens else ''
print('AI token 就绪:', bool(ai_tok))

if ai_tok:
    print('\n=== [2] 路径/方法矩阵 ===')
    paths = ['/ai-gateway/openai/v1/models', '/ai-gateway/openai/v1/responses',
             '/ai-gateway/openai/v1/chat/completions', '/openai/v1/models', '/openai/v1/chat/completions',
             '/v1/models', '/v1/chat/completions', '/chat/completions', '/models', '/responses', '/']
    for p in paths:
        for m in ('GET', 'POST'):
            body = {'model': 'gpt-4o-mini', 'messages': [{'role': 'user', 'content': 'hi'}]} if m == 'POST' and 'completions' in p or m == 'POST' and p == '/responses' else None
            st, raw = req(AI, m, p, body, {'Authorization': 'Bearer ' + ai_tok})
            tag = '%s %s' % (m, p)
            print('[%s] -> %d %s' % (tag[:52], st, raw[:160]))
            time.sleep(0.2)
            if st == 200 or (st == 400 and 'error' in raw[:50].lower()):
                break
        # 只测 GET 一次 + POST 一次即可, 减少噪音

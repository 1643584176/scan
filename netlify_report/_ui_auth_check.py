# -*- coding: utf-8 -*-
# _ui_auth_check.py - verify A/B creds still valid (api + app domain)
import sys, os, json, urllib.request, urllib.error

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _net_creds import TOKEN_A, TOKEN_B, COOKIE_A, COOKIE_B, USER_A, TEAM_A, TEAM_B

def req(method, url, tok=None, cookie=None, timeout=15):
    r = urllib.request.Request(url, method=method)
    if tok:
        r.add_header('Authorization', 'Bearer ' + tok)
    if cookie:
        r.add_header('Cookie', cookie)
    try:
        with urllib.request.urlopen(r, timeout=timeout) as resp:
            body = resp.read(600)
            try:
                return resp.status, resp.headers.get('Content-Type', '')[:40], json.loads(body.decode('utf-8', 'replace')) if 'json' in resp.headers.get('Content-Type', '') else body[:300]
            except Exception:
                return resp.status, resp.headers.get('Content-Type', '')[:40], body[:300]
    except urllib.error.HTTPError as e:
        b = e.read(400)
        try:
            return e.code, e.headers.get('Content-Type', '')[:40], json.loads(b.decode('utf-8', 'replace'))
        except Exception:
            return e.code, e.headers.get('Content-Type', '')[:40], b[:200]
    except Exception as ex:
        return -1, 'ERR', str(ex)[:200]

print('== TOKEN_A on api.netlify.com ==')
s, ct, b = req('GET', 'https://api.netlify.com/api/v1/user', tok=TOKEN_A)
print(s, ct, json.dumps(b, ensure_ascii=False)[:300] if isinstance(b, dict) else b)

print('== COOKIE_A on app.netlify.com ==')
s, ct, b = req('GET', 'https://app.netlify.com/api/v1/user', cookie=COOKIE_A)
print(s, ct, json.dumps(b, ensure_ascii=False)[:300] if isinstance(b, dict) else b)

print('== COOKIE_A teams ==')
s, ct, b = req('GET', 'https://app.netlify.com/api/v1/accounts?user_id=%s' % USER_A, cookie=COOKIE_A)
print(s, ct, json.dumps(b, ensure_ascii=False)[:400] if isinstance(b, dict) else b)

print('== TOKEN_B on api.netlify.com ==')
s, ct, b = req('GET', 'https://api.netlify.com/api/v1/user', tok=TOKEN_B)
print(s, ct, json.dumps(b, ensure_ascii=False)[:300] if isinstance(b, dict) else b)

print('== COOKIE_B teams ==')
s, ct, b = req('GET', 'https://app.netlify.com/api/v1/accounts?user_id=6a97b6454fef0db964f75db4', cookie=COOKIE_B)
print(s, ct, json.dumps(b, ensure_ascii=False)[:400] if isinstance(b, dict) else b)

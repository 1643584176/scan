# -*- coding: utf-8 -*-
"""检查两个账号 token 可用性 + 当前沙箱状态 (解析 authorization=Bearer 格式)"""
import json, re, urllib.request, urllib.error

def load_tok(path):
    raw = open(path, encoding='utf-8', errors='replace').read().strip()
    m = re.search(r'authorization=\s*Bearer\s+(\S+)', raw, re.I)
    if m:
        return m.group(1)
    m = re.search(r'Bearer\s+(\S+)', raw)
    if m:
        return m.group(1)
    return raw

def api_get(url, tok):
    req = urllib.request.Request(url, headers={
        'Authorization': 'Bearer ' + tok,
        'Content-Type': 'application/json',
        'User-Agent': 'scan-agent/1.0',
    })
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            body = r.read().decode('utf-8', errors='replace')
            return r.status, body
    except urllib.error.HTTPError as e:
        body = e.read().decode('utf-8', errors='replace')
        return e.code, body
    except Exception as e:
        return -1, '%s' % e

tok1 = load_tok(r'F:\scan\vercel_cookies.txt')
try:
    tok2 = load_tok(r'F:\scan\vercel_cookies2.txt')
except Exception:
    tok2 = None

print('tok1 len=%d head=%s' % (len(tok1), tok1[:12]))
c, r = api_get('https://api.vercel.com/v2/user', tok1)
print('user1 ->', c, r[:200])
c, r = api_get('https://api.vercel.com/v2/teams', tok1)
print('teams1 ->', c, r[:400])

if tok2:
    print('tok2 len=%d head=%s' % (len(tok2), tok2[:12]))
    c, r = api_get('https://api.vercel.com/v2/user', tok2)
    print('user2 ->', c, r[:200])
    c, r = api_get('https://api.vercel.com/v2/teams', tok2)
    print('teams2 ->', c, r[:400])

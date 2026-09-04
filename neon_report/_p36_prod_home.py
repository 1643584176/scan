# -*- coding: utf-8 -*-
"""prod 首页抓取: 确认 bundle URL -> 下载主 chunk -> 搜 so 定义/observability 端点主机"""
import http.client, ssl, re, os, sys, json

ctx = ssl.create_default_context()
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _neon_creds_prod import API_HOST, cookie_str

def get(path, host=API_HOST, extra=None):
    conn = http.client.HTTPSConnection(host, context=ctx, timeout=30)
    h = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0 Safari/537.36',
         'Cookie': cookie_str(), 'Accept': 'text/html,application/xhtml+xml,application/json;q=0.9,*/*;q=0.8'}
    if extra:
        h.update(extra)
    conn.request('GET', path, headers=h)
    r = conn.getresponse()
    raw = r.read()
    st = r.status
    hdrs = dict((k.lower(), v) for k, v in r.getheaders())
    conn.close()
    return st, raw, hdrs

st, raw, hdrs = get('/')
print('GET / ->', st, 'len', len(raw), flush=True)
txt = raw.decode('utf-8', 'ignore')
# 找 script src
scripts = re.findall(r'<script[^>]+src="([^"]+)"', txt)
print('scripts:', scripts[:20], flush=True)
# 找 next data / build id
m = re.search(r'"buildId":"([^"]+)"', txt)
print('buildId:', m.group(1) if m else None, flush=True)
# 找 chunk 引用
for s in scripts:
    if 'app' in s or 'main' in s or '.js' in s:
        print('candidate:', s, flush=True)

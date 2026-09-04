# -*- coding: utf-8 -*-
"""公开侦察2b: app.supabase.com 308 重定向目标 + dashboard bundle 定位"""
import http.client, ssl, re, os

ctx = ssl.create_default_context()
here = os.path.dirname(os.path.abspath(__file__))

def get(host, path):
    try:
        conn = http.client.HTTPSConnection(host, context=ctx, timeout=20)
        conn.request('GET', path, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/126.0'})
        r = conn.getresponse()
        loc = r.getheader('Location', '')
        raw = r.read()
        conn.close()
        return r.status, loc, raw
    except Exception as e:
        return -1, '', str(e).encode()

# 1. 跟随重定向
for h, p in [('app.supabase.com', '/'), ('dashboard.supabase.com', '/'), ('supabase.com', '/dashboard')]:
    st, loc, body = get(h, p)
    print('%s %s -> %s %s' % (h, p, st, loc[:120]), flush=True)
    if st == 200 and len(body) > 1000:
        fn = os.path.join(here, '_sb02_%s.html' % h.split('.')[0])
        open(fn, 'w', encoding='utf-8').write(body.decode('utf-8', 'ignore'))
        print('  saved', fn, 'len', len(body), flush=True)
        for mm in re.finditer(r'<script[^>]+src="([^"]+)"', body.decode('utf-8', 'ignore')):
            print('  SCRIPT:', mm.group(1)[:150], flush=True)
        for mm in re.finditer(r'<link[^>]+rel="[^"]*preload[^"]*"[^>]+href="([^"]+)"', body.decode('utf-8', 'ignore')):
            print('  PRELOAD:', mm.group(1)[:150], flush=True)

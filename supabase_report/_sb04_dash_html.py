# -*- coding: utf-8 -*-
"""公开侦察2c: supabase.com/dashboard 的 HTML -> JS chunk 定位下载"""
import http.client, ssl, re, os

ctx = ssl.create_default_context()
here = os.path.dirname(os.path.abspath(__file__))

def get(host, path):
    try:
        conn = http.client.HTTPSConnection(host, context=ctx, timeout=20)
        conn.request('GET', path, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/126.0', 'Accept': 'text/html'})
        r = conn.getresponse()
        loc = r.getheader('Location', '')
        raw = r.read()
        conn.close()
        return r.status, loc, raw
    except Exception as e:
        return -1, '', str(e).encode()

# dashboard 路径(未认证可能跳 sign-in)
for p in ['/dashboard/org', '/dashboard/projects', '/dashboard/sign-in']:
    st, loc, body = get('supabase.com', p)
    print('%s -> %s %s len=%d' % (p, st, loc[:100], len(body)), flush=True)
    if st == 200 and len(body) > 3000:
        html = body.decode('utf-8', 'ignore')
        fn = os.path.join(here, '_sb04_dash%s.html' % p.replace('/', '_'))
        open(fn, 'w', encoding='utf-8').write(html)
        sc = set(re.findall(r'<script[^>]+src="([^"]+)"', html))
        print('  scripts:', flush=True)
        for s in sorted(sc):
            print('   ', s[:180], flush=True)
        break

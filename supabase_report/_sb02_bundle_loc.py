# -*- coding: utf-8 -*-
"""公开侦察2: dashboard bundle 定位下载(app.supabase.com JS 无需认证)
找入口 html -> chunk 列表"""
import http.client, ssl, re, os

ctx = ssl.create_default_context()
here = os.path.dirname(os.path.abspath(__file__))

def get(host, path):
    try:
        conn = http.client.HTTPSConnection(host, context=ctx, timeout=20)
        conn.request('GET', path, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/126.0'})
        r = conn.getresponse()
        raw = r.read()
        conn.close()
        return r.status, raw
    except Exception as e:
        return -1, str(e).encode()

st, body = get('app.supabase.com', '/')
print('app.supabase.com / ->', st, len(body), flush=True)
if st == 200:
    html = body.decode('utf-8', 'ignore')
    open(os.path.join(here, '_sb02_home.html'), 'w', encoding='utf-8').write(html)
    # 找 script 标签
    for mm in re.finditer(r'<script[^>]+src="([^"]+)"', html):
        print('SCRIPT:', mm.group(1), flush=True)
    # chunkmap 或 modulepreload
    for mm in re.finditer(r'<link[^>]+href="([^"]+\.js)"', html):
        print('LINK JS:', mm.group(1), flush=True)
    # 内嵌 JSON 状态(可能含 csrf)
    m = re.search(r'<script[^>]*>([^<]{0,200})', html)

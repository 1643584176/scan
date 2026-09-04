# -*- coding: utf-8 -*-
"""Netlify 侦察 3:下载 app bundle 并提取端点"""
import http.client, ssl, gzip, brotli, re, os

ctx = ssl.create_default_context()

def get(host, path):
    conn = http.client.HTTPSConnection(host, context=ctx, timeout=30)
    conn.request('GET', path, headers={
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0',
        'Accept-Encoding': 'br, gzip'})
    r = conn.getresponse()
    raw = r.read()
    enc = r.getheader('Content-Encoding')
    if enc == 'br':
        raw = brotli.decompress(raw)
    elif enc == 'gzip':
        raw = gzip.decompress(raw)
    conn.close()
    return raw

# 从 net_app.html 提取所有 /assets/js/*.js 引用
html = open(r'D:\scan\netlify_report\_js\net_app.html', encoding='utf-8', errors='ignore').read()
jsfiles = re.findall(r'src="(/assets/js/[^"]+\.js)"', html)
print('JS files:', len(jsfiles))
for jf in jsfiles:
    name = jf.split('/')[-1].split('.')[0]
    try:
        raw = get('app.netlify.com', jf)
        path = r'D:\scan\netlify_report\_js\net_%s.js' % name
        open(path, 'wb').write(raw)
        print('  %-16s %7d' % (name, len(raw)))
    except Exception as e:
        print('  %-16s ERR %s' % (name, str(e)[:50]))

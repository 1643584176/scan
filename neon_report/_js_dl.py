# -*- coding: utf-8 -*-
"""下载主 bundle 并 grep org_id 相关调用上下文"""
import http.client, ssl, re, sys
ctx = ssl.create_default_context()

conn = http.client.HTTPSConnection('d216pytvakpmhr.cloudfront.net', context=ctx, timeout=120)
conn.request('GET', '/assets/app-CcBRprEu.js', headers={'User-Agent': 'Mozilla/5.0', 'Accept-Encoding': 'gzip'})
r = conn.getresponse()
raw = r.read()
ce = r.getheader('Content-Encoding')
conn.close()
if ce == 'gzip':
    import gzip
    raw = gzip.decompress(raw)
txt = raw.decode('utf-8', 'replace')
print('bundle len:', len(txt))
open(r'D:\scan\neon_report\_js\app.js', 'w', encoding='utf-8').write(txt)

# grep 错误文案的上下文
for kw in ['org_id is required', 'organization settings page']:
    for m in re.finditer(re.escape(kw), txt):
        i = m.start()
        print('\nCTX[%s]:' % kw, txt[max(0, i - 400):i + 200].replace('\n', ' ')[:600])

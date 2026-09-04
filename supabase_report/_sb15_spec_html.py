# -*- coding: utf-8 -*-
"""公开侦察15: Scalar 页面内 spec URL/内嵌 spec 提取"""
import http.client, ssl, os, re, json

here = os.path.dirname(os.path.abspath(__file__))
ctx = ssl.create_default_context()
c = http.client.HTTPSConnection("api.supabase.com", timeout=15, context=ctx)
c.request("GET", "/api/v1/openapi.json", headers={"User-Agent": "Mozilla/5.0"})
r = c.getresponse()
body = r.read().decode('utf-8', errors='replace')
c.close()
out = ['status %d len %d' % (r.status, len(body))]
open(os.path.join(here, '_sb15_spec_page.html'), 'w', encoding='utf-8').write(body)

# 1. 所有 URL 形态引用
for m in re.finditer(r'(?:href|src|url|spec|content)\s*[=:]\s*["\']([^"\']{0,200}(?:json|yaml|yml|spec)[^"\']{0,80})["\']', body, re.I):
    u = m.group(1)
    if not u.startswith(('data:', 'javascript')):
        out.append('REF: %s' % u[:220])

# 2. 常见 spec 挂载点字符串
for kw in ['openapi', 'scalar', 'cdn', '_spec', 'spec-url', 'specUrl']:
    for m in re.finditer(kw, body, re.I):
        i = m.start()
        seg = body[max(0, i - 150):i + 250].replace('\n', ' ')
        out.append('KW %s @%d: %s' % (kw, i, seg[:380]))
        break  # 只取首个

# 3. 内嵌 JSON spec 判断
i = body.find('"openapi"')
out.append('openapi-key @%d: %s' % (i, body[i:i + 300].replace('\n', ' ') if i >= 0 else 'NOT FOUND'))
open(os.path.join(here, '_sb15_spec.txt'), 'w', encoding='utf-8').write('\n'.join(out))
print('\n'.join(out[:40]))

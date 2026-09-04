# -*- coding: utf-8 -*-
"""拉取 Vercel 官方 OpenAPI spec, 列出 sandbox 相关端点全集 (公开文档, 对照已测面)"""
import json, sys, urllib.request, time
sys.stdout.reconfigure(encoding='utf-8')

def fetch(url, timeout=30):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read().decode('utf-8', 'replace')
    except Exception as e:
        return 0, str(e)[:200]

for url in ['https://api.vercel.com/openapi.json', 'https://openapi.vercel.com/openapi.json',
            'https://vercel.com/api/www/openapi.json']:
    c, body = fetch(url)
    print(url, '->', c, 'len=%d' % len(body))
    if c == 200 and body.startswith('{'):
        open(r'F:\scan\reports\_vercel_openapi.json', 'w', encoding='utf-8').write(body)
        try:
            spec = json.loads(body)
            print('  title:', spec.get('info', {}).get('title'))
            print('  paths:', len(spec.get('paths', {})))
        except Exception as e:
            print('  parse err:', e)
        break
    time.sleep(1)

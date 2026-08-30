# -*- coding: utf-8 -*-
import sys, urllib.request, urllib.error
sys.stdout.reconfigure(encoding='utf-8')
urls = [
    'https://openapi.vercel.com/openapi.json',
    'https://raw.githubusercontent.com/vercel/api/main/openapi.json',
    'https://raw.githubusercontent.com/vercel/vercel/main/packages/cli/src/util/get-teams.ts',
]
for url in urls:
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            body = r.read()
            print(url, '->', r.status, 'len=%d' % len(body), body[:80])
    except urllib.error.HTTPError as e:
        print(url, '-> HTTP', e.code, e.read()[:100])
    except Exception as e:
        print(url, '-> ERR', type(e).__name__, str(e)[:150])

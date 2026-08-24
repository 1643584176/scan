# -*- coding: utf-8 -*-
import io, sys, json
import urllib.request
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
raw=io.open('ws_cookie_A_new.txt',encoding='utf-8').read().strip().replace('\n','; ')
def get(url):
    req=urllib.request.Request(url, headers={'Cookie':raw,'User-Agent':'Mozilla/5.0'})
    try:
        return json.loads(urllib.request.urlopen(req, timeout=30).read())
    except Exception as e:
        return {'_err': str(e)[:120]}
for url in [
    'https://www.figma.com/api/recent-files',
    'https://www.figma.com/api/files/recent',
    'https://www.figma.com/api/user/recent_files',
]:
    d=get(url)
    keys=list(d.keys()) if isinstance(d,dict) else []
    print(url.split('api/')[-1], '->', keys[:8])
    if 'meta' in d and isinstance(d.get('meta'),list):
        m=d['meta'][0] if d['meta'] else {}
        print('  sample:', json.dumps(m,ensure_ascii=False)[:300])

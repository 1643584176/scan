# -*- coding: utf-8 -*-
import io, sys, json, time
import urllib.request
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
raw=io.open('ws_cookie_A_new.txt',encoding='utf-8').read().strip().replace('\n','; ')
def get(url):
    req=urllib.request.Request(url, headers={'Cookie':raw,'User-Agent':'Mozilla/5.0','accept':'application/json'})
    try:
        return json.loads(urllib.request.urlopen(req, timeout=25).read())
    except Exception as e:
        return {'_err': str(e)[:100]}
# 社区搜索
d=get('https://www.figma.com/api/community/search?query=component%20library&resource_type=file&page=1&page_size=10')
print('search keys:', list(d.keys()))
meta=d.get('meta',{})
items=meta if isinstance(meta,list) else meta.get('files',meta.get('items',[]))
print('items:', len(items) if isinstance(items,list) else '?')
for it in (items[:8] if isinstance(items,list) else []):
    print('  ', json.dumps({k:it.get(k) for k in ('id','name','file_key','fileKey','key')},ensure_ascii=False))

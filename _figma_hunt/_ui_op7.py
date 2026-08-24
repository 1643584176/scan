# -*- coding: utf-8 -*-
import io, sys, json
import urllib.request
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
raw=io.open('ws_cookie_A_new.txt',encoding='utf-8').read().strip().replace('\n','; ')
def get(url):
    req=urllib.request.Request(url, headers={'Cookie':raw,'User-Agent':'Mozilla/5.0'})
    return json.loads(urllib.request.urlopen(req, timeout=30).read())
d=get('https://www.figma.com/api/files/bv2nMIdFf4u3dESGail4sm')
meta=d.get('meta',{})
print('meta keys:', list(meta.keys()))
print('has document:', 'document' in meta)
# 尝试带参数
d2=get('https://www.figma.com/api/files/bv2nMIdFf4u3dESGail4sm?geometry=paths&depth=2')
m2=d2.get('meta',{})
print('depth2 meta keys:', list(m2.keys()))

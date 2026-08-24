# -*- coding: utf-8 -*-
import io, sys, json
import urllib.request
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
raw=io.open('ws_cookie_A_new.txt',encoding='utf-8').read().strip().replace('\n','; ')
def get(url, cookie=None):
    h={'Cookie':cookie or raw,'User-Agent':'Mozilla/5.0','accept':'application/json'}
    req=urllib.request.Request(url, headers=h)
    try:
        r=urllib.request.urlopen(req, timeout=30)
        return r.status, json.loads(r.read().decode('utf-8',errors='replace'))
    except Exception as e:
        return 'ERR', str(e)[:150]
FK='ucha7bf05fJ81CJZVoruo0'
st,d=get(f'https://www.figma.com/api/design_systems/library/{FK}/published_components?include_thumbnail=false&include_realtime=false')
print('published:', st)
if isinstance(d,dict):
    comps=d.get('meta',{}).get('components',[])
    print('components:', len(comps))
    if comps:
        c=comps[0]
        print('sample:', json.dumps(c,ensure_ascii=False)[:400])
st2,d2=get(f'https://www.figma.com/api/files/{FK}')
print('file:', st2)
if isinstance(d2,dict) and 'meta' in d2:
    m=d2['meta']
    print('name:', m.get('name'), '| link_access:', m.get('link_access'), '| creator:', m.get('creator_id'), '| library_key:', m.get('library_key'))

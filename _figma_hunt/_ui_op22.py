# -*- coding: utf-8 -*-
import io, sys, json
import urllib.request
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
rawA=io.open('ws_cookie_A_new.txt',encoding='utf-8').read().strip().replace('\n','; ')
rawB=io.open('ws_cookie_B_new.txt',encoding='utf-8').read().strip().replace('\n','; ')
def get(url, cookie=None):
    h={'Cookie':cookie or rawA,'User-Agent':'Mozilla/5.0','accept':'application/json'}
    req=urllib.request.Request(url, headers=h)
    try:
        r=urllib.request.urlopen(req, timeout=30)
        return r.status, r.read().decode('utf-8',errors='replace')
    except Exception as e:
        return 'ERR', str(e)[:150]
FK='ucha7bf05fJ81CJZVoruo0'
st,b=get(f'https://www.figma.com/api/design_systems/library/{FK}/published_components?include_thumbnail=false&include_realtime=false')
d=json.loads(b)
c=d['meta']['components'][0]
print('FULL comp:', json.dumps(c,ensure_ascii=False)[:800])
# 也取第2/3个组件对比
for i in (1,2,500):
    cc=d['meta']['components'][i]
    print(f'[{i}]', json.dumps({k:cc.get(k) for k in ('name','component_key','asset_id','type')},ensure_ascii=False))

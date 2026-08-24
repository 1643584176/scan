# -*- coding: utf-8 -*-
import io, sys, json, time
import urllib.request
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
rawB=io.open('ws_cookie_B_new.txt',encoding='utf-8').read().strip().replace('\n','; ')
def get(url):
    h={'Cookie':rawB,'User-Agent':'Mozilla/5.0','accept':'application/json,text/plain,*/*',
       'Origin':'https://www.figma.com','Referer':'https://www.figma.com/file/ucha7bf05fJ81CJZVoruo0/Flowbite'}
    req=urllib.request.Request(url, headers=h)
    try:
        r=urllib.request.urlopen(req, timeout=40)
        return r.status, r.read().decode('utf-8',errors='replace')
    except Exception as e:
        return 'ERR', str(e)[:150]
FK='ucha7bf05fJ81CJZVoruo0'
for i in range(3):
    st,b=get(f'https://www.figma.com/api/design_systems/library/{FK}/published_and_moved_components')
    print(f'try{i}:', st, b[:200])
    if st==200:
        d=json.loads(b)
        print('keys:', list(d.get('meta',{}).keys()) if isinstance(d.get('meta'),dict) else type(d.get('meta')))
        meta=d.get('meta',{})
        comps=meta.get('components',meta.get('published_components',[])) if isinstance(meta,dict) else []
        print('components:', len(comps))
        if comps:
            print('SAMPLE:', json.dumps(comps[0],ensure_ascii=False)[:700])
        break
    time.sleep(5)

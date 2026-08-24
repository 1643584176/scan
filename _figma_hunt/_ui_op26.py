# -*- coding: utf-8 -*-
import io, sys, json
import urllib.request
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
rawB=io.open('ws_cookie_B_new.txt',encoding='utf-8').read().strip().replace('\n','; ')
LK_FB='lk-a7138b8b7cc90989d1c018989dc4594f4282ff7efd909a62c7be6b3a490017ae756d5c31236d561d28c39b6022b3711ce36fcf88a2c71150d8fc47a6e53b171a'
def call(url, method='POST', body=None):
    h={'Cookie':rawB,'User-Agent':'Mozilla/5.0','accept':'application/json,text/plain,*/*','content-type':'application/json',
       'Origin':'https://www.figma.com','Referer':'https://www.figma.com/file/ucha7bf05fJ81CJZVoruo0/Flowbite'}
    req=urllib.request.Request(url, method=method, headers=h)
    if body is not None: req.data=json.dumps(body).encode()
    try:
        r=urllib.request.urlopen(req, timeout=30)
        return r.status, r.read().decode('utf-8',errors='replace')
    except Exception as e:
        return 'ERR', str(e)[:150]
# B 对 Flowbite 库创建单个 map(真实组件 14530:85888)
body={"library_key":LK_FB,"node_id":"14530:85888","template":"","component_name":"Type=Add condition, Dark Mode=True, Mobile=False",
      "source_path":"src/components/Condition.tsx","language":"React","status":"connected","origin":"mcp_local","entrypoint":""}
st,b=call('https://www.figma.com/api/code_connect/map','POST',body)
print('map B->Flowbite:', st)
print(b[:500])

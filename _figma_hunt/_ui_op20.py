# -*- coding: utf-8 -*-
import io, sys, json
import urllib.request
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
rawA=io.open('ws_cookie_A_new.txt',encoding='utf-8').read().strip().replace('\n','; ')
rawB=io.open('ws_cookie_B_new.txt',encoding='utf-8').read().strip().replace('\n','; ')
LK='lk-a7138b8b7cc90989d1c018989dc4594f4282ff7efd909a62c7be6b3a490017ae756d5c31236d561d28c39b6022b3711ce36fcf88a2c71150d8fc47a6e53b171a'
NODE='2454:33861'
CNAME='Type=Advanced Inputs, Dark Mode=False, Mobile=True'
def call(url, method='GET', body=None, cookie=None):
    h={'Cookie':cookie or rawB,'User-Agent':'Mozilla/5.0','accept':'application/json,text/plain,*/*','content-type':'application/json',
       'Origin':'https://www.figma.com','Referer':'https://www.figma.com/file/ucha7bf05fJ81CJZVoruo0/Flowbite'}
    req=urllib.request.Request(url, method=method, headers=h)
    if body is not None: req.data=json.dumps(body).encode()
    try:
        r=urllib.request.urlopen(req, timeout=30)
        return r.status, r.read().decode('utf-8',errors='replace')
    except Exception as e:
        return 'ERR', str(e)[:200]
# 0) B 身份确认 + 文件可读
st,b=call(f'https://www.figma.com/api/files/ucha7bf05fJ81CJZVoruo0')
print('B read file:', st, b[:120])
# 1) B 对 Flowbite 库 bulk_map(最小 body)
payload={
  "assets_to_map":[{"library_key":LK,"node_id":NODE,"component_name":CNAME,"source_path":"src/components/Input.tsx","status":"connected"}],
  "assetKeys":["SymbolId:454af72d828366a196271cc796918922fed0fc2c/2454:33861"],
  "libraryKey":LK
}
st,b=call('https://www.figma.com/api/code_connect/bulk_map','POST',payload)
print('bulk_map B->Flowbite:', st, b[:400])

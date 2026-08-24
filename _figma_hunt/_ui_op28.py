# -*- coding: utf-8 -*-
import io, sys, json
import urllib.request
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
rawB=io.open('ws_cookie_B_new.txt',encoding='utf-8').read().strip().replace('\n','; ')
LK_FB='lk-a7138b8b7cc90989d1c018989dc4594f4282ff7efd909a62c7be6b3a490017ae756d5c31236d561d28c39b6022b3711ce36fcf88a2c71150d8fc47a6e53b171a'
FK='ucha7bf05fJ81CJZVoruo0'
def call(url, body):
    h={'Cookie':rawB,'User-Agent':'Mozilla/5.0','accept':'application/json,text/plain,*/*','content-type':'application/json',
       'Origin':'https://www.figma.com','Referer':f'https://www.figma.com/file/{FK}/Flowbite'}
    req=urllib.request.Request(url, method='POST', headers=h, data=json.dumps(body).encode())
    try:
        r=urllib.request.urlopen(req, timeout=30)
        return r.status, r.read().decode('utf-8',errors='replace')[:260]
    except Exception as e:
        return 'ERR', str(e)[:150]
def t(label, payload):
    st,b=call('https://www.figma.com/api/code_connect/bulk_map', payload)
    print(f'{label}: {st} {b}')
a={"library_key":LK_FB,"node_id":"14530:85888","component_name":"Type=Add condition, Dark Mode=True, Mobile=False","source_path":"src/components/Condition.tsx","status":"connected"}
t('v5 lk=filekey', {"assets_to_map":[{**a,"library_key":FK}],"assetKeys":["14530:85888"],"libraryKey":FK})
t('v6 assetid-keys', {"assets_to_map":[a],"assetKeys":["SymbolId:a0fcbe9a8e871566baf7fff5e917e753a3c713b6/2454:33843"],"libraryKey":LK_FB})
t('v7 lk-filekey+assetid', {"assets_to_map":[{**a,"library_key":FK}],"assetKeys":["SymbolId:a0fcbe9a8e871566baf7fff5e917e753a3c713b6/2454:33843"],"libraryKey":FK})
t('v8 2assets', {"assets_to_map":[a,{**a,"node_id":"14530:85888","component_name":"X2"}],"assetKeys":["14530:85888"],"libraryKey":LK_FB})

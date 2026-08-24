# -*- coding: utf-8 -*-
import io, sys, json
import urllib.request, urllib.error
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
rawB=io.open('ws_cookie_B_new.txt',encoding='utf-8').read().strip().replace('\n','; ')
h={'Cookie':rawB,'User-Agent':'Mozilla/5.0','accept':'application/json,text/plain,*/*','content-type':'application/json',
   'Origin':'https://www.figma.com','Referer':'https://www.figma.com/files'}
req=urllib.request.Request('https://www.figma.com/api/mcp/session_token_exchange', method='POST', headers=h,
                           data=json.dumps({"client":"MCP_CLIENT_DESKTOP_PROXY"}).encode())
try:
    r=urllib.request.urlopen(req, timeout=25)
    print('status:', r.status)
    for k,v in r.headers.items():
        print(f'  {k}: {v}')
    body=r.read().decode('utf-8',errors='replace')
    print('body:', body[:300])
except urllib.error.HTTPError as e:
    print('HTTPError:', e.code)
    for k,v in e.headers.items():
        print(f'  {k}: {v}')
    print('body:', e.read().decode('utf-8',errors='replace')[:300])
except Exception as e:
    print('ERR:', str(e)[:150])

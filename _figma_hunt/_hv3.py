# -*- coding: utf-8 -*-
import io, sys, json
import urllib.request, urllib.error
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
rawB=io.open('ws_cookie_B_new.txt',encoding='utf-8').read().strip().replace('\n','; ')
def call(url, method='POST', body=None):
    h={'Cookie':rawB,'User-Agent':'Mozilla/5.0','accept':'application/json,text/plain,*/*','content-type':'application/json',
       'Origin':'https://www.figma.com','Referer':'https://www.figma.com/files'}
    req=urllib.request.Request(url, method=method, headers=h)
    if body is not None: req.data=json.dumps(body).encode()
    try:
        r=urllib.request.urlopen(req, timeout=25)
        return r.status, r.read().decode('utf-8',errors='replace')
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode('utf-8',errors='replace')
    except Exception as e:
        return 'ERR', str(e)[:150]

for client in ['MCP_CLIENT_DESKTOP_PROXY','MCP_CLIENT_WEB','MCP_CLIENT_DESKTOP','figma-mcp','test']:
    st,b=call('https://www.figma.com/api/mcp/session_token_exchange','POST',{"client":client})
    print(f'client={client}: {st} {b[:300]}')

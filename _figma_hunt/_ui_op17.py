# -*- coding: utf-8 -*-
import io, sys, json, time
import urllib.request
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
raw=io.open('ws_cookie_A_new.txt',encoding='utf-8').read().strip().replace('\n','; ')
AUID='1666382703778278399'
def call(url, method='POST', body=None, extra=None):
    h={'Cookie':raw,'User-Agent':'Mozilla/5.0','accept':'application/json,text/plain,*/*','content-type':'application/json','X-Figma-User-ID':AUID}
    if extra: h.update(extra)
    req=urllib.request.Request(url, method=method, headers=h)
    if body is not None: req.data=json.dumps(body).encode()
    try:
        r=urllib.request.urlopen(req, timeout=30)
        return r.status, r.read().decode('utf-8',errors='replace')
    except Exception as e:
        return 'ERR', str(e)[:200]
# 复制设计系统模板到 A 的草稿
for cid in ['1055785285964148921']:
    st, body = call(f'https://www.figma.com/api/hub_files/v2/{cid}/copy', 'POST', {})
    print(f'copy {cid}: {st} {body[:300]}')
    # 202 则等待重试
    for i in range(4):
        if st==202:
            time.sleep(15)
            st, body = call(f'https://www.figma.com/api/hub_files/v2/{cid}/copy', 'POST', {})
            print(f'  retry{i}: {st} {body[:200]}')
    if st==200:
        try:
            key=json.loads(body)['meta']['key']
            print('NEW FILE KEY:', key)
            st2,b2=call(f'https://www.figma.com/api/design_systems/library/{key}/published_components?include_thumbnail=false&include_realtime=false','GET')
            print('published_components:', st2, b2[:400])
        except Exception as e:
            print('parse err', str(e)[:150])

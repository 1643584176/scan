# -*- coding: utf-8 -*-
"""h1x22: bugs.json 端点家族变体探测(匿名,对照公开/私有报告)"""
import sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import requests, urllib3
urllib3.disable_warnings()

s = requests.Session()
s.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0.0.0 Safari/537.36'})

PUB = '2487889'   # 公开对照(应返回)
PRIV = '3732660'  # 私有(应拒绝)

paths = [
    '/bugs.json',
    '/reports/{}/bugs.json',
    '/bugs.json?report_id={}',
    '/bugs.json?report={}',
    '/report/{}/bugs.json',
    '/reports/{}.json',
    '/api/v1/reports/{}.json',
    '/reports/{}/export.json',
    '/reports/{}/export',
    '/report_export/{}.json',
    '/hacktivity.json',
    '/reports/{}/bug.json',
]

for p in paths:
    for rid in ([PUB] if '{}' in p else ['']):
        url = 'https://hackerone.com' + p.format(rid)
        try:
            r = s.get(url, timeout=15, allow_redirects=False)
            ct = r.headers.get('content-type', '')
            body = r.text[:200].replace('\n', ' ')
            print(f'[{r.status_code}] {url}  ct={ct[:40]}  body={body[:150]}')
        except Exception as e:
            print(f'[ERR] {url} {e}')
    print()

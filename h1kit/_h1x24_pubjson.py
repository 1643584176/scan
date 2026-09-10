# -*- coding: utf-8 -*-
"""h1x24: 抓公开报告 2487889 完整 .json(找 bugs.json PoC 端点形态)"""
import sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import requests, urllib3
urllib3.disable_warnings()

s = requests.Session()
s.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0.0.0 Safari/537.36'})

r = s.get('https://hackerone.com/reports/2487889.json', timeout=20)
print('status', r.status_code)
j = r.json()
print('top keys:', list(j.keys()))
print('full JSON:')
print(json.dumps(j, indent=1, ensure_ascii=False)[:6000])

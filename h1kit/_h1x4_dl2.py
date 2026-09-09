# -*- coding: utf-8 -*-
"""h1x4: 下载 app + vendor chunk"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import requests, urllib3
urllib3.disable_warnings()

s = requests.Session()
s.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0.0.0 Safari/537.36'})

for name, path in [('app', '/assets/static/app-5pKgUmmm.js'), ('vendor', '/assets/static/vendor-_WdvpBLr.js')]:
    r = s.get('https://hackerone.com' + path, timeout=120)
    print(f'{name}: {r.status_code} len {len(r.text)}')
    open(rf'D:\scan\h1kit\_h1x4_{name}.js', 'w', encoding='utf-8', errors='ignore').write(r.text)

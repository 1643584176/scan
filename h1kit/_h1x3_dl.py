# -*- coding: utf-8 -*-
"""h1x3: 下载 main bundle + constants, 分析端点"""
import sys, io, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import requests, urllib3
urllib3.disable_warnings()

s = requests.Session()
s.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
})

for name, path in [('main', '/assets/static/main_js-C8aqSh54.js'), ('constants', '/assets/constants-8c6b9114a287cf6e797cf5394b7f1f0c7917d38e51fcf9f58fe7eee44feb6ae5.js')]:
    r = s.get('https://hackerone.com' + path, timeout=60)
    print(f'{name}: {r.status_code} len {len(r.text)}')
    open(rf'D:\scan\h1kit\_h1x3_{name}.js', 'w', encoding='utf-8', errors='ignore').write(r.text)

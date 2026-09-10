# -*- coding: utf-8 -*-
"""h1x2: 匿名抓 SPA 壳页面 -> 定位应用 JS bundle"""
import sys, io, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import requests, urllib3
urllib3.disable_warnings()

s = requests.Session()
s.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
})

for path in ['/security', '/hacktivity/overview', '/reports/2487889']:
    r = s.get('https://hackerone.com' + path, timeout=25)
    t = r.text
    print(f'== GET {path} -> {r.status_code} len {len(t)}')
    # 找 bundle script / link preload
    for pat in [r'<script[^>]+src="([^"]+)"', r'<link[^>]+href="([^"]+\.js[^"]*)"']:
        for u in re.findall(pat, t)[:15]:
            print('  ', u[:160])
    # 找内嵌数据标记
    for kw in ['window.__', 'application/json', 'csrf', '_token', 'react', 'api']:
        if kw in t.lower():
            i = t.lower().find(kw)
            print(f'  KW[{kw}]: ...{t[max(0,i-80):i+120]}...')
    break  # 先只分析 /security
open(r'D:\scan\h1kit\_h1x2_security.html', 'w', encoding='utf-8', errors='ignore').write(r.text)

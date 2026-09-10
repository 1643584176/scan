# -*- coding: utf-8 -*-
"""h1x1: 匿名抓 hackerone.com 首页 HTML -> 定位 JS bundle -> 下载"""
import sys, io, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import requests, urllib3
urllib3.disable_warnings()

s = requests.Session()
s.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
})

r = s.get('https://hackerone.com/', timeout=25)
print('GET / ->', r.status_code, 'len', len(r.text))
open(r'D:\scan\h1kit\_h1x1_home.html', 'w', encoding='utf-8', errors='ignore').write(r.text)
# 提取 script src
scripts = re.findall(r'<script[^>]+src="([^"]+)"', r.text)
print('scripts:')
for u in scripts[:30]:
    print('  ', u)
# 提取其他资源域
for d in sorted(set(re.findall(r'https?://([a-z0-9.-]+)', r.text)))[:40]:
    print('DOMAIN:', d)

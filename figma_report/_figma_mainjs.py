# -*- coding: utf-8 -*-
"""抓取 Figma 首页 HTML,提取主 bundle URL"""
import requests, urllib3, re
urllib3.disable_warnings()
S = requests.Session()
S.trust_env = False
S.proxies = {'http': None, 'https': None}
S.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                  'Accept-Encoding': 'br, gzip'})
r = S.get('https://www.figma.com/', timeout=15, verify=False)
print('status:', r.status_code, 'len:', len(r.text))
html = r.text
scripts = re.findall(r'<script[^>]+src="([^"]+)"', html)
print('scripts:', len(scripts))
for s in scripts[:30]:
    print('  ', s[:130])
mains = [s for s in scripts if 'figma_app' in s and s.endswith('.js')]
print('main bundles:', mains)

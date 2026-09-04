# -*- coding: utf-8 -*-
"""检查代理连通性 + 代理出口 IP"""
import requests, sys

PROXY = {'http': 'http://192.168.0.199:1080', 'https': 'http://192.168.0.199:1080'}

# 1. 走代理
try:
    r = requests.get('https://api.ipify.org', proxies=PROXY, timeout=8)
    print('PROXY OK, exit IP:', r.text.strip())
except Exception as e:
    print('PROXY FAIL:', e)

# 2. 直连
try:
    r = requests.get('https://api.ipify.org', timeout=8)
    print('DIRECT OK, exit IP:', r.text.strip())
except Exception as e:
    print('DIRECT FAIL:', e)

# 3. 目标可达性(走代理)
for url in ['https://openam-bug-bounty-stag.forgeblocks.com/', 'https://console.ort-one-pingone.com/']:
    try:
        r = requests.get(url, proxies=PROXY, timeout=10, verify=False, allow_redirects=False)
        print('TARGET %s -> %d %s' % (url, r.status_code, r.headers.get('Location', '')[:60]))
    except Exception as e:
        print('TARGET %s FAIL: %s' % (url, str(e)[:100]))

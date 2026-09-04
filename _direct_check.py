# -*- coding: utf-8 -*-
"""直连测试 Ping Identity 目标(禁用代理,忽略环境变量)"""
import requests, urllib3
urllib3.disable_warnings()

# 显式禁用代理:空 proxies + trust_env=False 双保险
S = requests.Session()
S.trust_env = False  # 忽略 HTTP_PROXY/HTTPS_PROXY 环境变量
S.proxies = {'http': None, 'https': None}

targets = [
    'https://openam-bug-bounty-stag.forgeblocks.com/',
    'https://console.ort-one-pingone.com/',
    'https://api.ipify.org',
]
for url in targets:
    try:
        r = S.get(url, timeout=10, verify=False, allow_redirects=False)
        loc = r.headers.get('Location', '')
        print('OK   %-55s -> %d %s' % (url, r.status_code, loc[:50]))
    except Exception as e:
        print('FAIL %-55s -> %s' % (url, str(e)[:90]))

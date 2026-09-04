# -*- coding: utf-8 -*-
"""agentic_provisioning 端点:OpenAPI 覆盖检查 + 实测"""
import json, http.client, ssl, re, html, sys, os, time

# 1. OpenAPI 检查
d = json.load(open('D:/scan/neon_report/_openapi_v2.json', encoding='utf-8'))
found = [p for p in d.get('paths', {}) if 'agentic' in p.lower() or 'account_request' in p.lower() or 'provision' in p.lower()]
print('openapi agentic paths:', found, flush=True)

# 2. JS 上下文(附近代码看调用参数)
t = open('D:/scan/neon_report/_js/app.js', encoding='utf-8', errors='ignore').read()
i = t.find('agentic_provisioning')
while i != -1:
    print('\n--- ctx @%d ---' % i)
    print(t[max(0, i - 700):i + 500][:1200])
    i = t.find('agentic_provisioning', i + 1)
    if i > 2000000:
        break

# -*- coding: utf-8 -*-
"""app.js 内容识别 + 宽匹配 API 路径"""
import re

t = open('D:/scan/neon_report/_js/app.js', encoding='utf-8', errors='ignore').read()

# 1. 这是什么页面: 特征
for feat in ['keycloak', 'login', 'register', 'signin', 'neon-console', 'staging', 'api/v2', 'projects']:
    print(feat, t.count(feat))

# 2. 宽匹配: fetch/axios/url 中的 api 路径
pats = set(re.findall(r'["\'`](/[a-zA-Z0-9_\-]{2,30}(?:/[a-zA-Z0-9_\-{}$.]+){0,5})["\'`]', t))
api = [p for p in pats if any(k in p for k in ['api', 'auth', 'project', 'org', 'user', 'key', 'branch', 'login', 'sign'])]
print('\nmatched:', len(api))
for p in sorted(api)[:150]:
    print(p)

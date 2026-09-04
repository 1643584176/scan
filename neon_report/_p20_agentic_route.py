# -*- coding: utf-8 -*-
"""找 agentic account request 页面路由 path + orchestrator 常量"""
import re

t = open('D:/scan/neon_report/_js/app.js', encoding='utf-8', errors='ignore').read()

# 1. 页面路由 path(Claim/agentic 相关)
for pat in [r'["\'`](/[a-zA-Z0-9_\-/:]*account[^"\'`]{0,60})["\'`]',
            r'["\'`](/[a-zA-Z0-9_\-/:]*agentic[^"\'`]{0,60})["\'`]',
            r'["\'`](/[a-zA-Z0-9_\-/:]*claim[^"\'`]{0,40})["\'`]']:
    found = sorted(set(re.findall(pat, t, re.I)))
    if found:
        print('PAT', pat[:40])
        for f in found[:30]:
            print('  ', f)

# 2. AgenticProvisioningAccountRequest 枚举定义附近(D.Root/D.Claim 是 route enum)
i = t.find('AgenticProvisioningAccountRequest')
print('\n--- enum ctx ---')
print(t[max(0, i - 1500):i + 300].replace('\n', ' ')[:2000])

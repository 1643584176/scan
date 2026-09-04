# -*- coding: utf-8 -*-
"""查找 MITM/init.sock 相关脚本 + 观测通道(DNSlog/webhook)配置"""
import os, re

D = r'F:\scan\skills\non-traditional-vuln-hunting'
print('=== 含 init.sock / MITM / SpawnService 的脚本 ===')
for f in sorted(os.listdir(D)):
    if not f.endswith('.py'): continue
    p = os.path.join(D, f)
    try:
        txt = open(p, encoding='utf-8', errors='replace').read()
    except Exception:
        continue
    if re.search(r'init\.sock|MITM|mitm|SpawnService|X-Signature', txt, re.I):
        print('  %s' % f)

print()
print('=== 观测通道配置 ===')
for f in ['fw_dnslog_domain.py', 'fw_webhook_token.py', 'fw_driver.py']:
    p = os.path.join(D, f)
    if os.path.exists(p):
        txt = open(p, encoding='utf-8', errors='replace').read()
        print('--- %s ---' % f)
        print(txt[:800])
        print()

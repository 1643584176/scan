# -*- coding: utf-8 -*-
"""主 bundle 中找 livegraph view 注册:已知名验证 + viewName 字面量 + subscribe 上下文"""
import re

d = open('D:/scan/figma_report/_js/figma_app-main.js', 'r', encoding='utf-8', errors='ignore').read()
print('len', len(d))

# 1. 已知 view 名是否在
for known in ['FileMakeVersionsView', 'PlanByFileKey', 'FilePermissionsView', 'FileMetaDataView',
              'FileUserStateView', 'TeamView', 'UserView']:
    print(known, '->', d.count(known))

# 2. viewName 字面量附近
print()
print('== viewName 附近 ==')
for m in list(re.finditer(r'viewName[^,;]{0,120}', d))[:20]:
    print('  ', m.group(0)[:140])

# 3. subscribe 消息构造
print()
print('== subscribe 构造 ==')
for m in list(re.finditer(r'[^,;]{0,80}subscribe[^,;]{0,120}', d))[:20]:
    g = m.group(0).strip()
    if 'view' in g.lower() or 'messageType' in g:
        print('  ', g[:160])

# 4. 字符串常量 "xxxView" 带引号的形式(注册表可能是字符串数组)
print()
print('== "XxxView" 字符串(带引号,像注册表) ==')
qv = set(re.findall(r'"([A-Za-z0-9]{4,60}View)"', d))
print('quoted View strings:', len(qv))
for v in sorted(qv):
    if v.endswith('View') and 'View' != v:
        print('  ', v)

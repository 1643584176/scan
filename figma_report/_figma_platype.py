# -*- coding: utf-8 -*-
"""查 planType/planParentType 有效枚举值 + MemberFlyout 调用点"""
import re

d = open('D:/scan/figma_report/_js/figma_app-main.js', 'r', encoding='utf-8', errors='ignore').read()

# 1. planType 字面量
print('== planType 字面量 ==')
for m in list(re.finditer(r'planType[:=]"[a-z_]+"', d))[:20]:
    print('  ', m.group(0))
for m in list(re.finditer(r'"planType"\s*:\s*"[a-z_]+"', d))[:20]:
    print('  ', m.group(0))

# 2. MemberFlyout 调用点
print()
print('== MemberFlyoutInfoView 调用 ==')
for m in list(re.finditer(r'.{150}MemberFlyoutInfoView.{150}', d))[:4]:
    print('  ', m.group(0).replace('\n', ' ')[:330])
print()
print('== MemberFlyoutInfoFromPlanUser 调用 ==')
for m in list(re.finditer(r'.{150}MemberFlyoutInfoFromPlanUser.{150}', d))[:4]:
    print('  ', m.group(0).replace('\n', ' ')[:330])

# 3. planType 枚举上下文
print()
print('== planType 附近 ==')
for m in list(re.finditer(r'planType[^a-zA-Z].{0,80}', d))[:30]:
    print('  ', m.group(0)[:100])

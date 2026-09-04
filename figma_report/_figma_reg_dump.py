# -*- coding: utf-8 -*-
"""提取高价值 view 的 args(批量 dump 注册表)"""
import re

d = open('D:/scan/figma_report/_js/figma_app-main.js', 'r', encoding='utf-8', errors='ignore').read()
# 提取整个注册表:o("Name",[args],"hash") 连续串
i0 = d.find('o("AccountTypeRequestByIdView"')
seg = d[i0:i0 + 400000]

names = re.findall(r'o\("([A-Za-z0-9_]+)",\[([^\]]*)\],"([0-9a-f]{40,})"\)', seg)
print('registry views:', len(names))

# 找高价值面
interest = ['Member', 'Plan', 'Org', 'Team', 'User', 'AiChat', 'Thread', 'Workspace',
            'Admin', 'Seat', 'Account', 'Billing', 'Checkout', 'Invoice', 'Payment',
            'Usage', 'Meter', 'Invite', 'File', 'Project', 'Folder', 'Session']
for n, args, h in names:
    if any(k.lower() in n.lower() for k in interest):
        print('%-52s args=[%s]' % (n, args[:90]))

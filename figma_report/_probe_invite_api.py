# -*- coding: utf-8 -*-
"""考古: /api/invites 及分享弹窗的邀请请求形态 (email/角色/payload)"""
import sys, io, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

data = open(r'D:\scan\figma_report\_js\figma_app-main.js', encoding='utf-8', errors='replace').read()

# 1. /api/invites 上下文
for kw in ['/api/invites', 'invitees', 'invite_email', 'emailsToInvite', 'share_dialog', 'role":"viewer"', "role:'viewer'"]:
    ms = list(re.finditer(re.escape(kw), data))
    print(f'===== [{kw}] x{len(ms)} =====')
    for m in ms[:4]:
        s = max(0, m.start() - 400)
        e = min(len(data), m.end() + 400)
        print(f'@{m.start()}: {data[s:e].replace(chr(10)," ")[:800]}')
        print()
print('ALL DONE')

# -*- coding: utf-8 -*-
"""h1x53s: 考古 agentic_ui_mcp + reports 子路径端点的调用上下文(uri 格式/资源类型/method)"""
import re, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
t = open(r'D:\scan\h1kit\_h1x4_app.js', encoding='utf-8', errors='ignore').read()

print('########## 1. agentic_ui_mcp 全上下文 ##########')
for m in list(re.finditer(r'agentic_ui_mcp', t)):
    j = m.start()
    print('--- @', j)
    print(t[max(0, j-700):j+900].replace('\n', ' ')[:1600])
    print()

print('\n########## 2. summaries / report_collaborators / external_users / invitations 上下文 ##########')
for pat in ['/reports/${', 'summaries', 'report_collaborators', 'external_users', 'collaborator_invitations']:
    hits = list(re.finditer(re.escape(pat), t))
    print(f'### {pat}: {len(hits)} hits')
    for m in hits[:5]:
        j = m.start()
        print('--- @', j)
        print(t[max(0, j-400):j+400].replace('\n', ' ')[:800])
        print()

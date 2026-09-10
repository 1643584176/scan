# -*- coding: utf-8 -*-
"""h1x53k: bundle 考古 ConversationEntry fragment + GetAgentConversationById 页面来源 + validation/exploit agent 页面"""
import re, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
t = open(r'D:\scan\h1kit\_h1x4_app.js', encoding='utf-8', errors='ignore').read()

# 1. ConversationEntry fragment 定义(找 fragment ConversationEntry on)
for m in list(re.finditer(r'fragment ConversationEntry on', t))[:3]:
    j = m.start()
    print('=' * 10, 'fragment ConversationEntry @', j)
    print(t[j:j+800].replace('\n', ' ')[:800])
    print()

# 2. GetAgentConversationById 使用方(找查询名 → 附近页面)
for m in list(re.finditer(r'GetAgentConversationById', t))[:4]:
    j = m.start()
    print('=' * 10, 'GetAgentConversationById @', j)
    print(t[max(0, j-600):j+300].replace('\n', ' ')[:900])
    print()

# 3. validation_agent_conversation / exploit_agent_conversation 上下文
for pat in ['validation_agent_conversation', 'exploit_agent_conversation']:
    for m in list(re.finditer(pat, t))[:3]:
        j = m.start()
        print('=' * 10, pat, '@', j)
        print(t[max(0, j-400):j+500].replace('\n', ' ')[:900])
        print()

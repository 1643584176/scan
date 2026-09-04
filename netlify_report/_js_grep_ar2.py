# -*- coding: utf-8 -*-
import re
t = open(r'D:\scan\netlify_report\_js\net_app.js', encoding='utf-8', errors='ignore').read()

# 1. agent-runner-file-upload 完整 mutation(响应解析)
i = t.find('agent-runner-file-upload')
seg = t[i - 800:i + 2500]
print('=== upload mutation ===')
print(seg.replace('\n', ' ')[:3000])
print()

# 2. accountId 传参来源(找 mutation 调用处)
for m in re.finditer(r'file-upload[^;]{0,80}', t):
    pass
j = t.find('mutationFn')
# 找 "accountId:" 出现在 agent 上下文
hits = [m.start() for m in re.finditer(r'accountId', t)]
print('accountId hits:', len(hits))
# 取其中 5 处上下文,找其赋值来源
shown = 0
for h in hits:
    s = max(0, h - 150)
    ctx = t[s:h + 150].replace('\n', ' ')
    if 'agent' in ctx.lower() or 'team' in ctx.lower():
        print('ctx:', ctx[:300])
        print('-----')
        shown += 1
        if shown >= 8:
            break

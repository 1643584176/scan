# -*- coding: utf-8 -*-
"""h1x53l: bundle 考古 - 找全部会话类型 gid TypePath(解码内嵌 id 常量)+ node(id) 全局解析逻辑"""
import re, sys, io, base64
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
t = open(r'D:\scan\h1kit\_h1x4_app.js', encoding='utf-8', errors='ignore').read()

print('===== 1. 明文 Conversations::Views:: 出现 =====')
hits = list(re.finditer(r'Conversations::Views::[A-Za-z]+', t))
print('count:', len(hits))
seen = set()
for m in hits:
    s = m.group(0)
    if s not in seen:
        seen.add(s)
        print(s)
print('unique:', sorted(seen))

print()
print('===== 2. base64 gid 前缀解码(gid://hackerone/Conversations) =====')
p = re.compile(r'[A-Za-z0-9+/]{40,}={0,2}')
decoded = set()
for m in p.finditer(t):
    s = m.group(0)
    try:
        d = base64.b64decode(s + '=' * (-len(s) % 4)).decode('utf-8', errors='ignore')
    except Exception:
        continue
    if d.startswith('gid://hackerone/') and 'Conversation' in d:
        # 只取类型路径部分
        body = d[len('gid://hackerone/'):]
        tp = body.rsplit('/', 1)[0]
        decoded.add(tp)
        if len(decoded) > 40:
            break
print('conversation TypePaths found:', sorted(decoded))

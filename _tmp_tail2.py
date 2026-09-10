# -*- coding: utf-8 -*-
"""读取 bf51118a 会话历史,输出尾部消息(assistant 文本 + 工具调用摘要)"""
import json, re

p = r'C:\Users\tndc2\.qoder\cache\projects\scan-72ece876\conversation-history\bf51118a\bf51118a.jsonl'
lines = open(p, encoding='utf-8', errors='replace').read().splitlines()
print('total lines:', len(lines))

out = []
# 先看结构:每行 role 分布
from collections import Counter
roles = Counter()
for ln in lines:
    try:
        o = json.loads(ln)
        roles[o.get('role')] += 1
    except Exception:
        roles['PARSE_ERR'] += 1
print('roles:', dict(roles))

# 输出最后 40 条的消息流
msgs = []
for ln in lines:
    try:
        o = json.loads(ln)
        msgs.append(o)
    except Exception:
        pass

print('parsed msgs:', len(msgs))
for o in msgs[-40:]:
    role = o.get('role')
    msg = o.get('message', {})
    c = msg.get('content')
    parts = []
    if isinstance(c, list):
        for part in c:
            if not isinstance(part, dict):
                parts.append(str(part)[:300])
                continue
            t = part.get('type')
            if t == 'text' or part.get('text'):
                txt = part.get('text') or ''
                m = re.search(r'<user_query>(.*?)</user_query>', txt, re.S)
                if m:
                    txt = m.group(1)
                else:
                    txt = re.sub(r'<ide_context>.*?</ide_context>', '[IDE]', txt, flags=re.S)
                    txt = re.sub(r'<system-reminder>.*?</system-reminder>', '[SYS]', txt, flags=re.S)
                parts.append('[TEXT] ' + txt[:2000])
            elif t == 'tool_use' or part.get('tool_calls') or part.get('name'):
                nm = part.get('name') or (part.get('function') or {}).get('name') or '?'
                inp = part.get('input') or (part.get('function') or {}).get('arguments') or ''
                parts.append('[TOOL %s] %s' % (nm, str(inp)[:400]))
            elif t == 'tool_result' or part.get('tool_call_id'):
                cc = part.get('content')
                parts.append('[RESULT] ' + str(cc)[:300])
            else:
                parts.append('[%s] %s' % (t, json.dumps(part, ensure_ascii=False)[:250]))
    else:
        parts.append(str(c)[:1500])
    out.append('===== %s =====' % role)
    out.extend(parts)
    out.append('')

open(r'D:\scan\_tmp_tail2_out.txt', 'w', encoding='utf-8').write('\n'.join(out))
print('written tail to _tmp_tail2_out.txt')

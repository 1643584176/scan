# -*- coding: utf-8 -*-
"""解析 _run_v169_out.txt, 找 init.sock 探测结果 (400/HIT 线索)"""
import json, re, sys

f = '_run_v169_out.txt'
lines = open(f, 'r', encoding='utf-8', errors='replace').read().splitlines()
print('TOTAL LINES:', len(lines))

hits = []
for ln in lines:
    try:
        obj = json.loads(ln)
    except Exception:
        continue
    # 找出 data 字段
    data = obj.get('data') or obj.get('output') or obj.get('log') or ''
    if not isinstance(data, str):
        data = str(data)
    # 解码 JSON 转义 (data 里可能本身是转义后的字符串)
    try:
        data2 = json.loads('"%s"' % data) if data.startswith('\\') or '\\u' in data else data
    except Exception:
        data2 = data
    if 'INIT' in data2 or '400' in data2 or 'HIT' in data2 or 'init' in data2.lower() and 'HTTP' in data2:
        hits.append((obj.get('ts') or obj.get('time') or '', data2[:2000]))

print('HITS:', len(hits))
seen = set()
for ts, d in hits:
    # 提取日志行
    for m in re.finditer(r'\[[\d.]+\] ([^\n]+)', d):
        line = m.group(1)
        if line not in seen:
            seen.add(line)
            print('%s | %s' % (ts, line[:1500]))

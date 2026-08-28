# -*- coding: utf-8 -*-
"""提取 Vercel 相关会话中的 API 端点与调用代码,输出到文件"""
import re, os, glob, datetime, json

BASE = r'C:\Users\tndc2\.qoder\cache\projects\scan-72ece876\conversation-history'
OUT = r'D:\scan\skills\non-traditional-vuln-hunting\vercel_api_recovered.txt'
TARGETS = ['1a7a395a', 'e1507845', '494b74ea', 'd1c9a155', '558c85f7', '8b33948a', '16ba677c', '478d0b50']

lines = []
for sid in TARGETS:
    fp = os.path.join(BASE, sid, sid + '.jsonl')
    if not os.path.exists(fp):
        continue
    with open(fp, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    lines.append('################ %s (%dKB) ################' % (sid, os.path.getsize(fp) // 1024))

    # 所有含 vercel api 的 URL
    urls = set(re.findall(r'https?://[^\s"\'\\,)\]]+', content))
    api_urls = sorted(u for u in urls if 'vercel.com' in u and ('api' in u or 'v1' in u or 'sandbox' in u or 'sbx' in u))
    if api_urls:
        lines.append('--- URL 候选 ---')
        for u in api_urls[:20]:
            lines.append(u[:200])

    # Authorization token / x-vercel header 上下文
    for kw in ['Authorization', 'x-vercel', 'Bearer ']:
        for m in re.finditer(re.escape(kw), content):
            s = max(0, m.start() - 150)
            seg = content[s:m.end() + 250].replace('\\n', '\n').replace('\\"', '"')
            lines.append('--- %s @%d ---' % (kw, m.start()))
            lines.append(seg[:400])
            break  # 每个文件每个关键词只看一处

    # python 代码块中的 sandbox 调用
    for m in re.finditer(r'def [a-z_]*(create|exec|run|sandbox)[a-z_]*\(', content):
        s = max(0, m.start() - 100)
        seg = content[s:m.start() + 600].replace('\\n', '\n').replace('\\"', '"')
        lines.append('--- func %s @%d ---' % (m.group(0), m.start()))
        lines.append(seg[:700])

with open(OUT, 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))
print('written:', OUT, len(lines), 'lines')

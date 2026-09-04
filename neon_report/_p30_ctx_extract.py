# -*- coding: utf-8 -*-
"""提取 assistants / observability-settings 端点上下文(方法/参数/语义)"""
import re, os

here = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(here, '_js', 'app.js'), encoding='utf-8', errors='replace').read()

for kw in ['assistants', 'observability-settings', 'observability']:
    print('=' * 70, flush=True)
    print('KEYWORD:', kw, flush=True)
    idxs = [m.start() for m in re.finditer(re.escape(kw), src)]
    print('occurrences:', len(idxs), flush=True)
    shown = 0
    for i in idxs[:6]:
        seg = src[max(0, i - 700):i + 700]
        # 只打印含 method 词或 URL 构造的片段
        print('--- ctx %d ---' % i, flush=True)
        print(seg[:1400].replace('\n', ' '), flush=True)
        shown += 1
        if shown >= 4:
            break

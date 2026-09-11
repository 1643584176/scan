# -*- coding: utf-8 -*-
# q76: 真空白端点精确核对 + 935 JS 里这些端点的方法/参数
import sys, io, glob, os, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

D = r'D:\scan\figma_report'
files = [f for f in glob.glob(os.path.join(D, '_*.py')) if '_q76' not in f]

# 精确串核对
exacts = [
    '/api/folders/rename', '/api/folders/restore', '/api/folders/trash',
    'last_interaction', 'source_file_updated_info', 'figment-proxy',
    'hub_file_duplicates', '/api/tagged_file', 'page_thumbnails',
    "/meta'", '/meta`', "'/meta'", '"meta"',
]
print('=== 精确串核对（排除 q76 自身）===')
for w in exacts:
    cnt = 0
    sample = ''
    for f in files:
        try:
            t = open(f, encoding='utf-8', errors='replace').read()
        except Exception:
            continue
        c = t.count(w)
        if c:
            cnt += c
            if not sample:
                i = t.find(w)
                sample = f'{os.path.basename(f)}: ...{t[max(0,i-70):i+70]}...'.replace('\n', ' ')
    flag = '**真空白**' if cnt == 0 else ''
    print(f'{w:34s} {cnt:4d}  {flag}')
    if sample:
        print(f'    {sample[:180]}')

# 935 JS 里这些端点的调用上下文
print('\n=== 935 JS 调用上下文 ===')
F = os.path.join(D, '_js', '935-431f89677a39072c.min.js')
t = open(F, encoding='utf-8', errors='replace').read()
for kw in ['last_interaction', 'source_file_updated_info', 'folders/rename', 'folders/restore', 'folders/trash', 'figment-proxy', 'hub_file_duplicates', 'tagged_file']:
    i = t.find(kw)
    print(f'\n--- {kw} @{i} ---')
    if i >= 0:
        st = max(0, i - 350)
        print(' ', t[st:i + 250].replace('\n', ' ')[:620])
print('DONE q76')

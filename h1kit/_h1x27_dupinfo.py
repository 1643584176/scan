# -*- coding: utf-8 -*-
"""h1x27: 提取 DuplicateInfoQuery 完整字符串 + 找 report_duplicates_page chunk + SortInput 字段"""
import re, sys, io, os, glob
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

t = open(r'D:\scan\h1kit\_h1x4_app.js', encoding='utf-8', errors='ignore').read()
out = []

# 1. DuplicateInfoQuery 字符串形式(若有)或 AST 后接区域
for m in re.finditer(r'"((?:[^"\\]|\\.)*query DuplicateInfoQuery(?:[^"\\]|\\.)*?)"', t):
    out.append('===== DuplicateInfoQuery string len=%d =====\n%s\n' % (len(m.group(1)), m.group(1).replace('\\n','\n')[:3000]))
    break
else:
    # AST 形式: 找它的 selectionSet 并转义打印 2500 字符
    i = t.find('DuplicateInfoQuery')
    while i != -1:
        seg = t[i:i+4000]
        if 'OperationDefinition' in t[max(0,i-200):i]:
            out.append('===== DuplicateInfoQuery AST ctx =====\n' + seg[:3500] + '\n')
            break
        i = t.find('DuplicateInfoQuery', i+1)

# 2. chunk 文件位置
for pat in [r'D:\scan\h1kit\*.js', r'D:\scan\h1kit\_js\*.js', r'D:\scan\h1kit\**\*.js']:
    for f in glob.glob(pat, recursive=True):
        if 'report_duplicates_page' in f or 'report_page' in f:
            out.append('chunk: ' + f)
out.append('h1kit dir listing:')
for f in sorted(os.listdir(r'D:\scan\h1kit'))[:60]:
    out.append('  ' + f)

# 3. SortInput 定义/枚举:找 search 调用处 sort 变量构造
out.append('--- SortInput 附近 ---')
i = t.find('SortInput')
while i != -1 and i < len(t):
    seg = t[max(0,i-100):i+600]
    if 'field' in seg or 'order' in seg:
        out.append('ctx: ...' + seg[:600].replace('\\n',' '))
        break
    i = t.find('SortInput', i+1)

open(r'D:\scan\h1kit\_h1x27_out.txt', 'w', encoding='utf-8').write('\n'.join(out))
print('\n'.join(out)[:3500])

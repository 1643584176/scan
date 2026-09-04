# -*- coding: utf-8 -*-
import collections, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
ls = [l[3:].rstrip('\n') for l in open(r'D:\scan\_tmp_untracked_all.txt', encoding='utf-8', errors='replace')]
# 顶层目录统计
c = collections.Counter(x.split('/')[0] for x in ls if '/' in x)
for k, v in sorted(c.items(), key=lambda t: -t[1]):
    print(v, k)
print('---- 仅顶层文件 ----')
for x in ls:
    if '/' not in x:
        print(x)

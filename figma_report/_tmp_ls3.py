# -*- coding: utf-8 -*-
import io, re, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
t = open('_sq1_map.txt', encoding='utf-8').read().splitlines()
doms = []
cur = None
names = []
for l in t:
    m = re.match(r'^-- ([a-z_0-9]+) \((\d+)\) --', l)
    if m:
        doms.append((m.group(1), int(m.group(2))))
print(f'未深测域总数: {len(doms)}')
for i, (d, n) in enumerate(doms):
    print(f'{i+1:3d}. {d} ({n})')
# 也统计全部段(含 DEEP/PART 域)找其他分区标题
print()
print('== 分区标题行 ==')
for l in t:
    if l.startswith('====='):
        print(l)

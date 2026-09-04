# -*- coding: utf-8 -*-
"""全资产搜 webpack-artifacts/chunk 映射/figma_app 引用"""
import re, os, glob

D = 'D:/scan/figma_report/_js/'

print('== webpack-artifacts 引用 ==')
for p in glob.glob(D + '*.min.js'):
    d = open(p, 'r', encoding='utf-8', errors='ignore').read()
    hits = re.findall(r'webpack-artifacts.{0,80}', d)
    for h in set(hits):
        print(os.path.basename(p), ':', h[:100])

print()
print('== 数字chunk->hash 映射(webpack u 函数) ==')
for p in glob.glob(D + '*.min.js'):
    d = open(p, 'r', encoding='utf-8', errors='ignore').read()
    # 形如 935:"431f89677a39072c" 或 935:"abc" 的映射对象
    for m in re.finditer(r'\{[^{}]*?\d{2,5}:"[0-9a-f]{6,40}"[^{}]*?\}', d):
        g = m.group(0)
        if g.count('":') > 5:
            print(os.path.basename(p), ':', g[:400])
            break

print()
print('== app_file.html 所有 figma_app 上下文 ==')
c = open(D + 'app_file.html', 'r', encoding='utf-8', errors='ignore').read()
for m in re.finditer(r'.{60}figma_app.{60}', c):
    print('  ', m.group(0).replace('\n', ' ')[:140])

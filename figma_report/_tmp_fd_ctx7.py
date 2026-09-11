# -*- coding: utf-8 -*-
"""挖 JS 7: et/Q 模块尾部(调用方) + versionHistory 填充 + fileVersion store"""
import io

F = r'D:\scan\figma_report\_js\figma_app-main.js'
t = io.open(F, encoding='utf-8', errors='ignore').read()

print('===== A) 2588500-2594000 (et 之后) =====')
print(t[2588500:2594000].replace('\n', ' '))

print()
print('===== B) versionHistory 命中(定义/填充) =====')
i = 0; n = 0
while True:
    i = t.find('versionHistory', i)
    if i < 0: break
    n += 1
    if n <= 14:
        print('-' * 12, 'hit', n, '@', i, '::', t[max(0, i - 240):i + 320].replace('\n', ' '))
        print()
    i += 14
print('total versionHistory hits:', n)
print('DONE7')

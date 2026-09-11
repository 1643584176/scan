# -*- coding: utf-8 -*-
"""挖 JS 8: API客户端 r(295502) 的头注入 + csrf/x-figma 头 + fileVersion store 来源"""
import io

F = r'D:\scan\figma_report\_js\figma_app-main.js'
t = io.open(F, encoding='utf-8', errors='ignore').read()

print('===== 1) 模块 295502 定义 =====')
for pat in ('295502(e,t,r)', '295502:', '"295502"'):
    i = t.find(pat)
    print('pattern', pat, '->', i)
    if i >= 0:
        print(t[i:i + 1500].replace('\n', ' '))
        break
print()

print('===== 2) x-figma / csrf 头注入 =====')
for term in ('x-figma', 'X-Figma', 'x-csrf', 'csrfToken', 'csrf_token'):
    i = 0; n = 0
    while True:
        i = t.find(term, i)
        if i < 0: break
        n += 1
        if n <= 6:
            print('-' * 12, term, 'hit', n, '@', i, '::', t[max(0, i - 260):i + 300].replace('\n', ' '))
            print()
        i += len(term)
    print('   total', term, ':', n)
print()

print('===== 3) fileVersion store 定义线索 =====')
for term in ('fileVersion:', 'SET_FILE_VERSION', 'file_version:'):
    i = 0; n = 0
    while True:
        i = t.find(term, i)
        if i < 0: break
        n += 1
        if n <= 10:
            print('-' * 12, term, 'hit', n, '@', i, '::', t[max(0, i - 260):i + 360].replace('\n', ' '))
            print()
        i += len(term)
    print('   total', term, ':', n)
print('DONE8')

# -*- coding: utf-8 -*-
"""挖 JS 5: 定位模块 475210 定义处(多种 webpack 形态)"""
import io

F = r'D:\scan\figma_report\_js\figma_app-main.js'
t = io.open(F, encoding='utf-8', errors='ignore').read()

print('===== 475210 全部出现 =====')
i = 0
cnt = 0
while True:
    i = t.find('475210', i)
    if i < 0:
        break
    cnt += 1
    print(cnt, '@', i, '::', t[i - 100:i + 160].replace('\n', ' '))
    print()
    i += 6
    if cnt > 40:
        print('... (truncated)')
        break
print('DONE5')

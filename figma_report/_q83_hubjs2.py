# -*- coding: utf-8 -*-
# q83: Y() 函数定义 + hub copy v2 完整上下文 + resource_uses schema 提取
import sys, io, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

D = r'D:\scan\figma_report\_js'
s = io.open(D + r'\figma_app-main.js', encoding='utf-8', errors='replace').read()

# 1) Y() 定义：找 "${Y(e)}" 所在模块里的函数定义
for m in list(re.finditer(r'function Y\(', s))[:6]:
    i = m.start()
    print('Y def >>>', s[i:i+200].replace('\n', ' ')[:200])

# 2) prepare_insert 上下文完整段（更大窗口）
m = re.search(r'function J\(\{template:e,fileKey:t,fileVersion:r\}\)', s)
if m:
    i = m.start()
    print('\n\nJ() full >>>', s[i:i+900].replace('\n', ' ')[:900])

# 3) resource_uses schema validator 上下文
m = re.search(r'ResourceUseSchemaValidator', s)
if m:
    i = m.start()
    print('\n\nResourceUseSchema >>>', s[max(0,i-500):i+500].replace('\n', ' ')[:1000])

# 4) 1491 js 里 v2 copy 完整段
try:
    s2 = io.open(D + r'\1491-748d1f965b422f2e.min.js', encoding='utf-8', errors='replace').read()
    m = re.search(r'hub_files/v2', s2)
    if m:
        i = m.start()
        print('\n\nv2copy >>>', s2[max(0,i-600):i+600].replace('\n', ' ')[:1200])
except Exception as e:
    print('1491 read err', e)

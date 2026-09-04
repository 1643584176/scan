# -*- coding: utf-8 -*-
"""查 requestIdManager.getRequestId 实现(本地生成 or 服务器获取)+ viewHasStaticQueries"""
import re

d = open('D:/scan/figma_report/_js/figma_app-main.js', 'r', encoding='utf-8', errors='ignore').read()
for m in list(re.finditer(r'.{150}requestIdManager.{200}', d))[:5]:
    print('---', m.group(0).replace('\n', ' ')[:360])
    print()
for m in list(re.finditer(r'.{100}viewHasStaticQueries.{150}', d))[:5]:
    print('===', m.group(0).replace('\n', ' ')[:260])
    print()
for m in list(re.finditer(r'getRequestId\s*[=(].{0,250}', d))[:5]:
    print('>>>', m.group(0).replace('\n', ' ')[:300])
    print()

# -*- coding: utf-8 -*-
"""bundle 中 AI 线程可见性语义:privacyMode 取值、UI 过滤逻辑、面板文案"""
import os, re

MAIN = r'F:/scan/figma_report/_js/figma_app-main.js'
with open(MAIN, encoding='utf-8', errors='ignore') as f:
    c = f.read()

print('=== privacyMode 上下文 ===')
for m in re.finditer(r'[^,;{}]{0,140}privacyMode[^,;{}]{0,140}', c):
    print('  ', m.group(0).replace('\n', ' ')[:280])

print()
print('=== ThreadsManager 过滤逻辑(userId 相关) ===')
for m in list(re.finditer(r'[^,;{}]{0,150}(?:threads?\.(?:filter|some)|filter\([^)]{0,80}userId|userId[^,;{}]{0,60}(?:===|!==)[^,;{}]{0,60})[^,;{}]{0,150}', c))[:15]:
    print('  ', m.group(0).replace('\n', ' ')[:300])

print()
print('=== AI 历史面板文案 ===')
for kw in ['Ask Figma', 'Your threads', 'your threads', 'thread history', 'Thread history', 'New thread', 'private thread', 'Only you']:
    for m in list(re.finditer(re.escape(kw), c))[:3]:
        i = m.start()
        ctx = c[max(0, i - 120):i + 150]
        print(f'  [{kw}] ...{ctx.replace(chr(10), " ")[:260]}...')

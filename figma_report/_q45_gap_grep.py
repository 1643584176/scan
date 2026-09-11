# -*- coding: utf-8 -*-
# 核查: thumbnails 的 fk 位 / 头位 历史打点 + notification_settings 的 recipient_settings/mass assignment 历史
import sys, io, os, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

files = [f for f in os.listdir('.') if f.startswith('_figma_r') and f.endswith('.py')]
print(f'扫描 {len(files)} 个脚本')
print()
print('### 1) videos/thumbnails 相关行（看 fk 位是否被变体过）')
for f in sorted(files):
    txt = open(f, encoding='utf-8', errors='replace').read()
    for i, line in enumerate(txt.splitlines(), 1):
        if 'videos' in line and ('thumbnails' in line or 'FILE_A' in line):
            print(f, i, '|', line.strip()[:180])
print()
print('### 2) X-Figma-User-ID 出现（找有无注入变体）')
for f in sorted(files):
    txt = open(f, encoding='utf-8', errors='replace').read()
    for i, line in enumerate(txt.splitlines(), 1):
        if 'User-ID' in line and ('+' in line or 'inject' in line or 'quote' in line or "\\'" in line):
            print(f, i, '|', line.strip()[:180])
print('（无输出=从未打过头位注入变体）')
print()
print('### 3) recipient_settings 历史行')
for f in sorted(files):
    txt = open(f, encoding='utf-8', errors='replace').read()
    for i, line in enumerate(txt.splitlines(), 1):
        if 'recipient_settings' in line:
            print(f, i, '|', line.strip()[:170])
print()
print('### 4) team_id/id 字段注入（mass assignment）历史')
hit = 0
for f in sorted(files):
    txt = open(f, encoding='utf-8', errors='replace').read()
    if 'notification_settings' not in txt:
        continue
    for i, line in enumerate(txt.splitlines(), 1):
        if re.search(r"'team_id'|\"team_id\"|'org_id'|\"org_id\"|'id':|mass", line):
            print(f, i, '|', line.strip()[:170]); hit += 1
print('（无输出=从未测过 mass assignment）' if hit == 0 else '')
print()
print('### 5) frequencies 元素类型（null/数字/对象/数组）历史')
hit = 0
for f in sorted(files):
    txt = open(f, encoding='utf-8', errors='replace').read()
    for i, line in enumerate(txt.splitlines(), 1):
        if re.search(r"frequencies.*\[(None|null|123|\{\}|\[\]|True|true)", line):
            print(f, i, '|', line.strip()[:170]); hit += 1
print('（无输出=只打过字符串元素）' if hit == 0 else '')

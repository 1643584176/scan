# -*- coding: utf-8 -*-
"""调试 deep90 文件解析"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

data = open(r'F:\scan\skills\out\deep33090_guest_20260829_134434.txt', 'rb').read().decode('utf-8', errors='replace')
print('raw len:', len(data))
print('BODY count in raw:', data.count('BODY'))
print('backslash-n count:', data.count('\\n'))

idx = data.find('BODY')
print('first BODY at:', idx)
print('context:', data[idx - 50:idx + 500])

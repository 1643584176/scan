# -*- coding: utf-8 -*-
"""提取 deep33090 输出的关键行"""
import sys, re
sys.stdout.reconfigure(encoding='utf-8')

data = open(r'F:\scan\skills\out\deep33090_guest_20260829_134434.txt', 'rb').read().decode('utf-8', errors='replace')

# 打印所有日志行 (把 \n 转义还原为换行)
data2 = data.replace('\\n', '\n').replace('\\r', '')
for ln in data2.splitlines():
    m = re.match(r'\[(\d+\.\d+)\] (.*)', ln)
    if m:
        print(m.group(2)[:600])

# -*- coding: utf-8 -*-
"""查看 rodata 中 token/URL 字符串周边的完整常量"""
import re

data = open(r'D:\scan\netlify_report\_ext_binary.bin', 'rb').read()
BASE = 0x368a50  # NETLIFY_FUNCTIONS_TOKEN 文件偏移
# 打印前后 600 字节,以 | 分隔可打印段
seg = data[BASE - 400:BASE + 800]
for m in re.finditer(rb'[\x20-\x7e]{4,}', seg):
    off = BASE - 400 + m.start()
    print('%#x: %r' % (off, m.group(0).decode('ascii')))

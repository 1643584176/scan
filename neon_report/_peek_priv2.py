# -*- coding: utf-8 -*-
import json

s = open(r'D:\scan\neon_report\_neonauth_priv.txt', encoding='utf-8').read().strip()
print('len:', len(s))
print('starts/ends:', s[0], s[-1])
inner = s.strip('"')
print('inner len:', len(inner))
# 检查非 hex 字符
bad = [c for c in inner if c not in '0123456789abcdefABCDEF']
print('non-hex chars:', bad[:10], 'count:', len(bad))
# 移除转义再看
import re
print('has \\n:', '\\n' in inner, '| has real newline:', '\n' in inner)
clean = inner.replace('\\n', '').replace('\\', '')
print('clean len:', len(clean), 'even:', len(clean) % 2 == 0)
try:
    b = bytes.fromhex(clean)
    print('hex bytes:', len(b))
except Exception as e:
    print('fromhex err:', e)

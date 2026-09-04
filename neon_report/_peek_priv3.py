# -*- coding: utf-8 -*-
s = open(r'D:\scan\neon_report\_neonauth_priv.txt', encoding='utf-8').read().strip().strip('"')
b = bytes.fromhex(s)
print('bytes:', len(b))
print(repr(b[:100]))
print(b[:200])

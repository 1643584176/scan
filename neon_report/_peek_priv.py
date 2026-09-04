# -*- coding: utf-8 -*-
raw = open(r'D:\scan\neon_report\_neonauth_priv.txt', 'rb').read()
print('bytes:', len(raw))
print('head:', raw[:80])
print('tail:', raw[-80:])
print('repr head:', repr(raw[:100]))

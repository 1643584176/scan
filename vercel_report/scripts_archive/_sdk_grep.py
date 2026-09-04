# -*- coding: utf-8 -*-
import re, sys
s = open(r'F:\scan\_sdk\package\dist\session.cjs', encoding='utf-8', errors='replace').read()
print('LEN', len(s))
for i, line in enumerate(s.splitlines()):
    low = line.lower()
    if 'interactive' in low or 'websocket' in low or 'token' in low or 'ws://' in low or 'wss://' in low:
        print(i, line[:160])

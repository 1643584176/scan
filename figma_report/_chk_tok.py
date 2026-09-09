# -*- coding: utf-8 -*-
import re
raw = open(r'D:\scan\figma_report\_w70b_curl.txt', encoding='utf-8').read()
m = re.search(r'Bearer (\S+)', raw)
print('match:', bool(m))
t = m.group(1)
print('len:', len(t))
print('head:', t[:60])
print('tail:', t[-60:])
i = t.find('auth_time')
print('auth_time idx:', i)
if i >= 0:
    print('segment:', t[max(0, i-20):i+240])
else:
    print('no auth_time in token! payload sample:', t[200:500])

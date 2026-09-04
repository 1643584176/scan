# -*- coding: utf-8 -*-
import io
p = r'D:\scan\netlify_report\api-endpoints.md'
d = open(p, encoding='utf-8').read()
print('lines:', d.count('\n') + 1)
print('v3 in file:', 'v3' in d)
print('first 6 lines:')
for l in d.split('\n')[:6]:
    print(' |', l[:80])

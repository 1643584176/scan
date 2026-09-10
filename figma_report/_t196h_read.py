# -*- coding: utf-8 -*-
import io, re
big = io.open('_r196f_h1.json', encoding='utf-8', errors='replace').read()
print('== h1 plan segments')
for m in re.finditer(r'\{[^{}]{0,400}"planId"[^{}]{0,400}\}', big):
    print('H1SEG>', m.group(0)[:420])
print()
print('== h1 planType mentions')
for m in re.finditer(r'.{80}planType.{120}', big):
    print('PT>', repr(m.group(0))[:220])
print()
for f in ['_r196f_h6.json', '_r196f_h7.json']:
    b = io.open(f, encoding='utf-8', errors='replace').read()
    i = b.find('buzzApprovalRequest')
    print(f, 'BUZZ>', repr(b[max(0, i - 160):i + 320])[:420] if i >= 0 else 'NONE')
    i2 = b.find('fileV2')
    print(f, 'FILEV2>', repr(b[max(0, i2 - 90):i2 + 300])[:340] if i2 >= 0 else 'NONE')
    print()
print('DONE')

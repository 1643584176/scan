# -*- coding: utf-8 -*-
"""从 v185 输出提取 SBC/SBI 的方法名(ControllerService/FileSystemService/SpawnService 归属)"""
import re

data = open(r'C:\Users\tndc2\.qoder\cache\projects\scan-72ece876\agent-tools\9aa693e0\4b2fe9d7.txt',
             encoding='utf-8', errors='replace').read()

# 找 SBC SERVICES 行完整内容
for m in re.finditer(r'SBC SERVICES\(\d+\): ([^\n]{0,2000})', data):
    print('SBC SVCS:', m.group(1)[:2000])
    break

# 方法归属: ControllerService/ FileSystemService/ SpawnService 后面的 token
for svc in ['ControllerService', 'FileSystemService', 'SpawnService']:
    toks = set()
    for mm in re.finditer(svc + r'/([A-Za-z]{2,40})', data):
        toks.add(mm.group(1))
    print('%s METHODS: %s' % (svc, ' '.join(sorted(toks))))

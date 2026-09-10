# -*- coding: utf-8 -*-
"""挖 JX InboxState 模型 url/fetch:数据端点与 subject 分支"""
import re, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
t = open(r'D:\scan\h1kit\_h1x4_app.js', encoding='utf-8', errors='ignore').read()

i = 7257412
# 向后 9000 字符找 url/fetch/subjects
seg = t[i:i+20000]
print('len seg', len(seg))
for m in re.finditer(r'(url[=:]|fetch\(|subjectIsUser|toJSON|sync|`/bugs\.json|GET|POST)', seg):
    j = m.start()
    ctx = seg[max(0, j-150):j+200].replace('\n', ' ')
    print('-' * 60)
    print(m.group(1), '@', i+j, ':', ctx[:350])

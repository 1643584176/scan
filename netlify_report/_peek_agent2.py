# -*- coding: utf-8 -*-
"""挖 agent-runner-file-upload 形态 + file_key 格式"""
import re

data = open(r'D:\scan\netlify_report\_js\net_app.js', encoding='utf-8', errors='ignore').read()

print('==== upload 引用 @20412 上下文(大窗口)====')
m = re.search('agent-runner-file-upload', data)
if m:
    s = max(0, m.start() - 3500)
    e = min(len(data), m.end() + 3500)
    print(data[s:e].replace('\n', ' '))
    print('=' * 80)

# 找 uploadFiles 的实现:搜索 file_key / fileKey 使用处
print('==== file_key / uploadFiles 实现线索 ====')
for key in ['file_key', 'uploadFiles', 'agent-runner-file-upload', 'FormData']:
    cnt = 0
    for mm in re.finditer(re.escape(key), data):
        s = max(0, mm.start() - 300)
        e = min(len(data), mm.end() + 300)
        seg = data[s:e].replace('\n', ' ')
        # 只打印包含 fetch/url/upload 语义的
        if any(x in seg for x in ('fetch', 'upload', 'body', 'form')):
            print('--- %s @%d ---' % (key, mm.start()))
            print(seg[:700])
            print('-' * 60)
            cnt += 1
            if cnt >= 3:
                break

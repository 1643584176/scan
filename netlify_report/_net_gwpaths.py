# -*- coding: utf-8 -*-
"""Netlify:搜 bundle 中 bb-api/analytics-api/set-auth/create-api 的完整路径拼接"""
import os, re

jsdir = r'D:\scan\netlify_report\_js'
for f in sorted(os.listdir(jsdir)):
    if not f.endswith('.js'):
        continue
    txt = open(os.path.join(jsdir, f), encoding='utf-8', errors='ignore').read()
    for kw in ['bb-api', 'analytics-api', 'set-auth', 'create-api', 'generate-access-control-token',
               'access-control']:
        for m in re.finditer(re.escape(kw), txt):
            i = m.start()
            ctx = txt[max(0, i - 600): i + 600]
            # 提取路径片段:紧邻的字符串字面量
            lits = re.findall(r'["\'`]((?:/[a-zA-Z0-9_\-${}.]+)+)["\'`]', ctx)
            # 找 fetch 调用格式
            fetches = re.findall(r'fetch\(\s*["\'`]?([^"\'`\s,]{4,100})', ctx)
            print('[%s] %s' % (f.replace('net_', '').replace('.js', ''), kw))
            if lits:
                print('  lits:', lits[:6])
            if fetches:
                print('  fetches:', fetches[:3])
            # 上下文前 150 字符
            print('  ctx:', ctx[:180].replace('\n', ' '))
            print()

# -*- coding: utf-8 -*-
"""Netlify:set-auth/create-api 调用上下文精确提取"""
import os, re

jsdir = r'D:\scan\netlify_report\_js'
for f in sorted(os.listdir(jsdir)):
    if not f.endswith('.js'):
        continue
    txt = open(os.path.join(jsdir, f), encoding='utf-8', errors='ignore').read()
    for kw in ['set-auth', 'create-api']:
        for m in re.finditer(re.escape(kw), txt):
            i = m.start()
            # 前后 3000 字符,找 fetch( 调用
            ctx = txt[max(0, i - 3000): i + 3000]
            for fm in re.finditer(r'fetch\(', ctx):
                j = fm.start()
                seg = ctx[j:j + 400]
                if kw in seg:
                    print('[%s] %s' % (f.replace('net_', '').replace('.js', ''), kw))
                    print('  fetch:', seg[:350].replace('\n', ' '))
                    print()
                    break
            # 找 .post(/.get( 调用
            for pm in re.finditer(r'\.(?:post|get|put|patch)\s*\(\s*["\'`]?([^"\'`\s,)]{5,120})', ctx):
                seg2 = ctx[pm.start():pm.start() + 300]
                if kw in seg2:
                    print('  method call:', seg2[:250].replace('\n', ' '))
                    print()

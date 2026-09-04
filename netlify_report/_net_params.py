# -*- coding: utf-8 -*-
"""Netlify:提取内部端点调用参数(从 bundle 上下文)"""
import os, re

jsdir = r'D:\scan\netlify_report\_js'
files = {}
for f in os.listdir(jsdir):
    if f.endswith('.js'):
        files[f] = open(os.path.join(jsdir, f), encoding='utf-8', errors='ignore').read()

targets = ['database-query', 'fetch-extension', 'install-extension', 'support-tickets',
           'generate-bandwidth-usage-csv', 'prompt-templates', 'knowledge',
           'fetch-extensions', 'extension-proxy', 'private-integration-create',
           'agent-runner-file-upload', 'labs-toggle', 'event-observed']

for t in targets:
    print('=' * 20, t)
    found = False
    for fname, txt in files.items():
        for m in re.finditer(re.escape(t), txt):
            i = m.start()
            ctx = txt[max(0, i - 2500): i + 1500]
            # 找调用上下文中的参数构造:JSON body、query 拼接
            # 1) 找 fetch/axios 调用的 body
            bodies = []
            for bm in re.finditer(r'(?:body|data|json|payload)\s*[:=]\s*(\{.{0,400}?\})', ctx, re.S):
                s = bm.group(1)[:400]
                if t[:8] in s or len(s) > 10:
                    bodies.append(s.replace('\n', ' ')[:380])
            # 2) query 参数拼接
            qs = re.findall(r'["\'+]([a-zA-Z_][a-zA-Z0-9_]*)=["\']?\s*\+', ctx)
            # 3) 参数名推断:上下文中的键
            keys = re.findall(r'["\']([a-zA-Z][a-zA-Z0-9_]*)["\']\s*:', ctx)
            keys = [k for k in keys if k not in ('type', 'content', 'href', 'target', 'rel', 'className', 'children', 'label', 'value', 'id', 'key', 'name', 'style')]
            print('  [%s]' % fname.replace('net_', '').replace('.js', ''))
            if bodies:
                print('    bodies:', bodies[:3])
            if qs:
                print('    query+:', qs[:8])
            if keys:
                print('    keys:', sorted(set(keys))[:15])
            # 上下文尾部(调用点)
            print('    ctx-tail:', ctx[-200:].replace('\n', ' ')[:180])
            found = True
            break
        if found:
            break
    print()

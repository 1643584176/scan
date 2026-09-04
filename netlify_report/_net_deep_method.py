# -*- coding: utf-8 -*-
"""Netlify v4:深挖未定方法端点的调用上下文(±3000 字符)"""
import os, re

jsdir = r'D:\scan\netlify_report\_js'
files = {}
for f in os.listdir(jsdir):
    if f.endswith('.js'):
        files[f] = open(os.path.join(jsdir, f), encoding='utf-8', errors='ignore').read()

targets = ['/.netlify/functions/extension-proxy', '/.netlify/functions/fetch-build-plugins',
           '/.netlify/functions/fetch-extension', '/.netlify/functions/fetch-extensions',
           '/.netlify/functions/fetch-installed-extensions-for-team',
           '/.netlify/functions/fetch-relevant-installed-extensions-for-site',
           '/.netlify/functions/identeer-proxy', '/.netlify/functions/labs-list',
           '/.netlify/functions/manage-extension-proxy', '/.netlify/functions/support-tickets',
           '/.netlify/functions/workflow-ui', '/.netlify/identity', '/.netlify/images',
           '/.netlify/large-media', '/access-control/analytics-api', '/access-control/bb-api',
           '/access-control/create-api', '/access-control/generate-access-control-token',
           '/access-control/set-auth', '/api/agent-runners/status', '/api/v1', '/api/v2/',
           '/spark-proxy/api/prompt-templates', '/v1/input', '/.netlify/builders/versions']

out = []
for t in targets:
    found = False
    for fname, txt in files.items():
        for m in re.finditer(re.escape(t), txt):
            i = m.start()
            ctx = txt[max(0, i - 3000): i + 3000]
            # 方法
            method = None
            for mm in ['POST', 'GET', 'PUT', 'DELETE', 'PATCH']:
                if re.search(r'method\s*[:=]\s*["\']%s["\']' % mm, ctx, re.I) or \
                   re.search(r'\.%s\s*\(' % mm.lower(), ctx) or \
                   re.search(r'["\']%s["\']\s*[,)]' % mm, ctx):
                    method = mm
                    break
            # body 字段
            body_keys = set()
            for bm in re.finditer(r'(?:data|body|params|payload|json|formData)\s*[:=]\s*(\{[^}]{0,300}\})', ctx):
                s = bm.group(1)
                for k in re.findall(r'["\']([a-zA-Z_][a-zA-Z0-9_]*)["\']\s*:', s):
                    body_keys.add(k)
            if not method and not body_keys:
                continue
            found = True
            out.append((t, method or '?', ','.join(sorted(body_keys))[:120] or '-', fname.replace('net_', '').replace('.js', '')))
            break
        if found:
            break
    if not found:
        out.append((t, '?', '-', '-'))

print('%-52s %-7s %-20s %s' % ('endpoint', 'method', 'body fields', 'caller'))
for t, m, b, c in out:
    print('%-52s %-7s %-20s %s' % (t, m, b, c))

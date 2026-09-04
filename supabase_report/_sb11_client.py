# -*- coding: utf-8 -*-
"""公开侦察9: 核心 API client chunk 提取:
1. 全部端点 path 字符串(platform/v1/replication/storage)
2. pg-meta query 调用函数上下文(impersonation 角色模拟机制)
"""
import re, os

here = os.path.dirname(os.path.abspath(__file__))
jsdir = os.path.join(here, '_sb_js')
fp = os.path.join(jsdir, '099kov3mfam-s.js')
src = open(fp, encoding='utf-8', errors='replace').read()
out = []

# 1. 全部 URL 形态(带 {ref}/:ref 模板)
paths = {}
for m in re.finditer(r'["\'`](/(?:platform|v1|storage|auth|rest|realtime)[^"\'`]{0,160})["\'`]', src):
    s = m.group(1)
    if ' ' in s or s.startswith('//'):
        continue
    paths.setdefault(s, 0)
    paths[s] += 1
out.append('=== ALL API paths (%d unique) ===' % len(paths))
for p, c in sorted(paths.items()):
    out.append('%3d %s' % (c, p[:170]))

# 2. pg-meta query 构造(找 query 函数体)
out.append('')
out.append('=== pg-meta/query 函数上下文 ===')
idxs = [m.start() for m in re.finditer(r'pg-meta', src)]
out.append('pg-meta occurrences: %d' % len(idxs))
for i in idxs[:6]:
    seg = src[max(0, i - 500):i + 500].replace('\n', ' ')
    out.append('@%d: %s' % (i, seg[:900]))

# 3. impersonation 相关
out.append('')
out.append('=== impersonation ===')
for m in re.finditer(r'impersonat\w*', src):
    i = m.start()
    seg = src[max(0, i - 300):i + 300].replace('\n', ' ')
    out.append('@%d: %s' % (i, seg[:560]))
    if len([x for x in re.finditer(r'impersonat\w*', src)]) > 12:
        break

open(os.path.join(here, '_sb11_client.txt'), 'w', encoding='utf-8').write('\n'.join(out))
print('lines:', len(out), flush=True)

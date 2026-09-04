# -*- coding: utf-8 -*-
"""公开侦察10: 0h9x8dhtehorj.js(39KB) 端点定义全提取 + safeSql/literal 实现"""
import re, os

here = os.path.dirname(os.path.abspath(__file__))
jsdir = os.path.join(here, '_sb_js')
fp = os.path.join(jsdir, '0h9x8dhtehorj.js')
src = open(fp, encoding='utf-8', errors='replace').read()
out = []
out.append('file size %d' % len(src))

# 1. 全部 path 字符串
paths = {}
for m in re.finditer(r'["\'`](/(?:platform|v1|storage|auth|rest|realtime|trpc)[^"\'`]{0,160})["\'`]', src):
    s = m.group(1)
    if ' ' in s or s.startswith('//'):
        continue
    paths.setdefault(s, 0)
    paths[s] += 1
out.append('=== paths (%d) ===' % len(paths))
for p, c in sorted(paths.items()):
    out.append('%3d %s' % (c, p[:180]))

# 2. 方法定义形态: getXxx/postXxx 函数名 + url
out.append('')
out.append('=== 函数定义(名称+路径) ===')
for m in re.finditer(r'([A-Za-z_$][\w$]*)\s*[=:]\s*(?:async\s*)?\([^)]*\)\s*=>\s*\{[^}]{0,400}?["\'`]([^"\'`]{0,140})["\'`]', src):
    nm, u = m.group(1), m.group(2)
    if u.startswith('/') and len(nm) > 2:
        out.append('%s -> %s' % (nm, u[:150]))

# 3. pg-meta query 调用处上下文
out.append('')
out.append('=== pg-meta/{ref}/query 上下文 ===')
for m in re.finditer(r'pg-meta', src):
    i = m.start()
    seg = src[max(0, i - 400):i + 400].replace('\n', ' ')
    out.append('@%d: %s' % (i, seg[:750]))
    if len(list(re.finditer(r'pg-meta', src))) > 8:
        break

open(os.path.join(here, '_sb12_dtl.txt'), 'w', encoding='utf-8').write('\n'.join(out))
print('lines:', len(out), flush=True)

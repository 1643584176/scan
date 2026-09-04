# -*- coding: utf-8 -*-
"""公开侦察8: 全量 grep 端点调用模式
1. pg-meta 相关字符串上下文
2. /platform/ /infrastructure/ /v1/ /projects 端点字符串
"""
import re, os, glob

here = os.path.dirname(os.path.abspath(__file__))
jsdir = os.path.join(here, '_sb_js')
out = []

# 模式1: URL 模板字符串(含 platform/pg-meta/v1/infrastructure)
urls = {}
for fn in sorted(glob.glob(os.path.join(jsdir, '*.js'))):
    src = open(fn, encoding='utf-8', errors='replace').read()
    for m in re.finditer(r'["\'`]([^"\'`]{0,40}(?:platform|pg-meta|/v1/|infrastructure|/projects)[^"\'`]{0,120})["\'`]', src):
        s = m.group(1)
        if ' ' in s or s.startswith('//') or s.startswith('http'):
            continue
        urls.setdefault(s, 0)
        urls[s] += 1

out.append('=== URL 字符串 (count) ===')
for u, c in sorted(urls.items(), key=lambda x: -x[1])[:120]:
    out.append('%3d  %s' % (c, u[:160]))

# 模式2: 取 pg-meta hit chunk 中 "query" 端点构造上下文
out.append('')
out.append('=== pg-meta chunk 详情 ===')
for name in ['099kov3mfam-s.js', '0h9x8dhtehorj.js', '0ktvwau299fo5.js', '0n7s33g1sgnzh.js', '135zu0645roqv.js', '21f3lz1qyh2dn.js', '22xhpobl2s5ti.js']:
    fp = os.path.join(jsdir, name)
    if not os.path.exists(fp):
        continue
    src = open(fp, encoding='utf-8', errors='replace').read()
    out.append('### %s (%d bytes)' % (name, len(src)))
    for m in re.finditer(r'pg-meta[^"\'`]{0,200}', src):
        out.append('   %s' % m.group(0)[:220])
        break
    # 找 endpoint 定义形态
    for m in re.finditer(r'["\'`]([^"\'`]{0,30}pg-meta[^"\'`]{0,150})["\'`]', src):
        out.append('   URL %s' % m.group(1)[:180])
    for m in re.finditer(r'(?:query|execute)[A-Za-z]*\s*[:=]\s*["\'`][^"\'`]{0,120}', src)[:0] if False else []:
        pass
open(os.path.join(here, '_sb10_endpoints.txt'), 'w', encoding='utf-8').write('\n'.join(out))
print('lines:', len(out), flush=True)

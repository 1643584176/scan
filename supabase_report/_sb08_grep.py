# -*- coding: utf-8 -*-
"""公开侦察6: 页面 chunk grep 端点面(platform/pg-meta/v1/query 等)"""
import re, os, glob

here = os.path.dirname(os.path.abspath(__file__))
jsdir = os.path.join(here, '_sb_js')
out = []
kws = ['platform/pg-meta', 'pg-meta', '/platform/', 'api.supabase.com', '/v1/', 'pg-meta/', 'query', 'executeSql', 'execute_sql']
for fn in sorted(glob.glob(os.path.join(jsdir, '*.js'))):
    try:
        src = open(fn, encoding='utf-8', errors='replace').read()
    except Exception as e:
        continue
    size = len(src)
    hits = []
    # 端点字符串形态: "platform/..." 或 "/platform/..." 或 "pg-meta/..."
    for m in re.finditer(r'["\'`]([^"\'`]{0,60}(?:pg-meta|platform|/v1/|/platform)[^"\'`]{0,90})["\'`]', src):
        s = m.group(1)
        if s.startswith('http') or '${' not in s[:20]:
            hits.append(s)
    # query 端点构造形态
    qh = re.findall(r'[A-Za-z_$][\w$]*\.query\s*[=(]', src)[:10]
    if hits or qh:
        out.append('### %s (%d bytes)' % (os.path.basename(fn), size))
        seen = set()
        for h in hits:
            if h not in seen:
                seen.add(h)
                out.append('  URL: %s' % h[:150])
        for q in qh:
            out.append('  query-call: %s' % q)
open(os.path.join(here, '_sb08_grep.txt'), 'w', encoding='utf-8').write('\n'.join(out))
print('done, lines:', len(out), flush=True)

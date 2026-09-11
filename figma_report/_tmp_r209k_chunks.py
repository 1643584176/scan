# -*- coding: utf-8 -*-
# r209k: 在多 chunk 中挖 in_context 调用点与 asset key 字段
import io, re, os, glob
d = os.path.dirname(os.path.abspath(__file__))
out = []
pat_files = ['_js/1272-39fc73641ce2f8dd.min.js', '_js/4227-d699909b39b89d9f.min.js',
             '_js/5557-4a9f5d8ca3c14987.min.js', '_js/5613-065a64a7ed9a322e.min.js',
             '_js/6958-dbb90408fc72f346.min.js', '_js/7435-ce1dc6726292bd56.min.js',
             '_js/935-431f89677a39072c.min.js']

for fp in pat_files:
    p = os.path.join(d, fp)
    if not os.path.exists(p):
        continue
    JS = io.open(p, encoding='utf-8', errors='replace').read()
    out.append('########## %s (%d bytes) ##########' % (os.path.basename(fp), len(JS)))
    for kw in ['in_context', 'asset_key', 'assetKey', 'published_components', 'code_connect']:
        idxs = [m.start() for m in re.finditer(re.escape(kw), JS)]
        if not idxs:
            continue
        out.append('===== %s :: %d hits =====' % (kw, len(idxs)))
        for i in idxs[:12]:
            seg = JS[max(0, i-250):i+400].replace('\n', ' ')
            out.append('  >>> ' + seg)
            out.append('  ---')
    out.append('')

io.open(os.path.join(d, '_r209k_chunks_out.txt'), 'w', encoding='utf-8').write('\n'.join(out))
print('DONE lines:', len(out))

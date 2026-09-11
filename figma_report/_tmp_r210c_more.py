# -*- coding: utf-8 -*-
# r210c: exportAsCsv URL + createCollection schema + 跨chunk调用方
import io, re, os
d = os.path.dirname(os.path.abspath(__file__))
JS = io.open(os.path.join(d, '_js/figma_app-main.js'), encoding='utf-8', errors='replace').read()
out = []

def ctx(kw, before=300, after=800, maxn=8, label=None):
    idxs = [m.start() for m in re.finditer(re.escape(kw), JS)]
    out.append('===== %s :: %d hits =====' % (label or kw, len(idxs)))
    for i in idxs[:maxn]:
        seg = JS[max(0, i - before):i + after].replace('\n', ' ')
        out.append('  >>> ' + seg)
        out.append('  ---')
    out.append('')

# exportAsCsv 完整
ctx('exportAsCsv', before=400, after=900, maxn=5, label='exportAsCsv 完整')
# createCollection 的 zod schema（CollectionResponseSchemaValidator 定义区）
ctx('CollectionSchemaValidator', before=800, after=300, maxn=6, label='CollectionSchemaValidator 区')
# FieldSchemaResponseValidator 区
ctx('FieldSchemaResponseValidator', before=500, after=200, maxn=6, label='FieldSchema 区')
# collection_id 用法
ctx('collection_id', before=300, after=500, maxn=8, label='collection_id 用法')

# 跨 chunk 调用方
jd = os.path.join(d, '_js')
out.append('===== 跨 chunk: claimTryFile / markInserted / createFieldSchema / exportAsCsv =====')
cnt = 0
for fn in sorted(os.listdir(jd)):
    if not fn.endswith('.js'):
        continue
    try:
        s = io.open(os.path.join(jd, fn), encoding='utf-8', errors='replace').read()
    except Exception:
        continue
    for kw in ['claimTryFile', 'markInserted(', 'createFieldSchema', 'exportAsCsv']:
        for m in re.finditer(re.escape(kw), s):
            i = m.start()
            seg = s[max(0, i - 200):i + 320].replace('\n', ' ')
            out.append('  [%s] %s >>> %s' % (fn, kw, seg))
            out.append('  ---')
            cnt += 1
out.append('跨 chunk 总命中: %d' % cnt)

io.open(os.path.join(d, '_r210c_ctx_out.txt'), 'w', encoding='utf-8').write('\n'.join(out))
print('DONE lines:', len(out))

# -*- coding: utf-8 -*-
# r210b: 三端点调用方 + 完整 schema + comments 写端点族
import io, re, os
d = os.path.dirname(os.path.abspath(__file__))
JS = io.open(os.path.join(d, '_js/figma_app-main.js'), encoding='utf-8', errors='replace').read()
out = []

def ctx(kw, before=300, after=500, maxn=20, label=None):
    idxs = [m.start() for m in re.finditer(re.escape(kw), JS)]
    out.append('===== %s :: %d hits =====' % (label or kw, len(idxs)))
    for i in idxs[:maxn]:
        seg = JS[max(0, i - before):i + after].replace('\n', ' ')
        out.append('  >>> ' + seg)
        out.append('  ---')
    out.append('')

# claimTryFile 完整 schema + 调用点
ctx('ClaimTryFileSchemaValidator', before=900, after=250, maxn=8, label='claim schema 定义区')
ctx('claimTryFile', before=200, after=400, maxn=10, label='claimTryFile 调用点')
# markInserted 调用点
ctx('.markInserted(', before=250, after=350, maxn=10, label='markInserted 调用点')
# createCollection 调用点
ctx('createCollection', before=300, after=600, maxn=10, label='createCollection 调用点')
# comments 写端点模板
ctx('comments/${', before=300, after=400, maxn=30, label='comments 全模板')
# field_type 枚举/用法
ctx('field_type', before=200, after=300, maxn=12, label='field_type 用法')

io.open(os.path.join(d, '_r210b_ctx_out.txt'), 'w', encoding='utf-8').write('\n'.join(out))
print('DONE lines:', len(out))

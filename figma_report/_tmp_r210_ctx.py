# -*- coding: utf-8 -*-
# r210: 单数族未打端点深挖（file collections / claim / mark_diagram_inserted / comments）
import io, re, os
d = os.path.dirname(os.path.abspath(__file__))
JS = io.open(os.path.join(d, '_js/figma_app-main.js'), encoding='utf-8', errors='replace').read()

out = []

def ctx(kw, before=280, after=480, maxn=25, label=None):
    idxs = [m.start() for m in re.finditer(re.escape(kw), JS)]
    out.append('===== %s :: %d hits =====' % (label or kw, len(idxs)))
    for i in idxs[:maxn]:
        seg = JS[max(0, i - before):i + after].replace('\n', ' ')
        out.append('  >>> ' + seg)
        out.append('  ---')
    out.append('')

# 1. mark_diagram_inserted
ctx('mark_diagram_inserted', label='mark_diagram_inserted')
# 2. claim（精准：file/claim 模板）
ctx('file/claim', label='file/claim 模板')
ctx('claimFile', label='claimFile 调用名')
# 3. /api/file/ collections 模板（精准：}/collections`）
ctx('}/collections`', label='file-collections 模板')
ctx('fileCollections', label='fileCollections')
# 4. comments 单数族调用点（找 fetch 函数名）
ctx('comments/${e.commentThreadId}`', before=400, after=300, maxn=15, label='comments thread 模板上下文')
ctx('deleteComment', label='deleteComment')
ctx('postComment', label='postComment')

io.open(os.path.join(d, '_r210_ctx_out.txt'), 'w', encoding='utf-8').write('\n'.join(out))
print('DONE lines:', len(out))

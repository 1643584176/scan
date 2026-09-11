# -*- coding: utf-8 -*-
# r209: 三未测面深挖 + /api/file/ 单数路径族全量
import io, re, os
d = os.path.dirname(os.path.abspath(__file__))
JS = io.open(os.path.join(d, '_js/figma_app-main.js'), encoding='utf-8', errors='replace').read()

out = []

# 1. /api/file/ 单数路径族全量（url 模板）
pat = re.compile(r'url`/api/file/[^`]{0,160}`')
hits = sorted(set(pat.findall(JS)))
out.append('===== url`/api/file/ (singular) :: %d unique =====' % len(hits))
for h in hits:
    out.append('  ' + h)
out.append('')

# 2. 各面 API 模板与上下文
for kw in ['/api/code_connect', 'voting_sessions', 'canvas_mentions', 'startVotingSession', 'getCanvasMentions', 'recordCanvasMention', 'postVoting', 'in_progress']:
    idxs = [m.start() for m in re.finditer(re.escape(kw), JS)]
    out.append('===== %s :: %d hits =====' % (kw, len(idxs)))
    for i in idxs[:25]:
        seg = JS[max(0, i-250):i+450].replace('\n', ' ')
        out.append('  >>> ' + seg)
        out.append('  ---')
    out.append('')

io.open(os.path.join(d, '_r209_ctx_out.txt'), 'w', encoding='utf-8').write('\n'.join(out))
print('DONE lines:', len(out))

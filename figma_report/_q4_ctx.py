# -*- coding: utf-8 -*-
# q4: related_links/canvas_mentions/voting 深度上下文
import io, re, os
d = os.path.dirname(os.path.abspath(__file__))
JS = io.open(os.path.join(d, '_js/figma_app-main.js'), encoding='utf-8', errors='replace').read()

kws = ['getRelatedLinks', 'related_links', 'linkPreviewJson', 'LINK_PREVIEW',
       'can_request_edit', 'needs_invite', 'votingSession', 'VotingSession',
       'realtime_token', 'page_thumbnails']
out = []
for k in kws:
    idxs = [m.start() for m in re.finditer(re.escape(k), JS)]
    out.append('===== %s :: %d hits =====' % (k, len(idxs)))
    lim = 12 if k in ('related_links', 'getRelatedLinks', 'can_request_edit') else 6
    for i in idxs[:lim]:
        seg = JS[max(0, i - 160):i + 320].replace('\n', ' ')
        out.append('  >>> ' + seg)
    out.append('')
io.open(os.path.join(d, '_q4_out.txt'), 'w', encoding='utf-8').write('\n'.join(out))
for k in kws:
    print(k, len(re.findall(re.escape(k), JS)))
print('DONE -> _q4_out.txt')

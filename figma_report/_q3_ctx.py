# -*- coding: utf-8 -*-
# q3: JS 中未测面关键词上下文提取
import io, re, os
d = os.path.dirname(os.path.abspath(__file__))
JS = io.open(os.path.join(d, '_js/figma_app-main.js'), encoding='utf-8', errors='replace').read()

kws = ['code_connect', 'related_links', 'link_preview', 'page_thumbnails',
       'recent_activity', 'realtime_token', 'voting_sessions', 'canvas_mentions',
       'feed_posts', 'asset_transfer', 'design_systems/bundles', 'figment-proxy',
       'checkpoint_diff', 'seller', 'arkose', 'related_links']
out = []
seen = set()
for k in kws:
    if k in seen:
        continue
    seen.add(k)
    idxs = [m.start() for m in re.finditer(re.escape(k), JS)]
    out.append('===== %s :: %d hits =====' % (k, len(idxs)))
    for i in idxs[:10]:
        seg = JS[max(0, i - 150):i + 280].replace('\n', ' ')
        out.append('  >>> ' + seg)
    out.append('')
io.open(os.path.join(d, '_q3_ctx_out.txt'), 'w', encoding='utf-8').write('\n'.join(out))
for k in kws:
    print(k, len(re.findall(re.escape(k), JS)))
print('DONE -> _q3_ctx_out.txt')

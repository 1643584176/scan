# -*- coding: utf-8 -*-
# r209m: 挖 voting_sessions POST requestBody 调用方构造（字段名）
import io, re, os
d = os.path.dirname(os.path.abspath(__file__))
JS = io.open(os.path.join(d, '_js/figma_app-main.js'), encoding='utf-8', errors='replace').read()

out = []
for m in re.finditer(r'requestBody', JS):
    i = m.start()
    seg = JS[max(0, i-400):i+600].replace('\n', ' ')
    if 'vot' in seg.lower():
        out.append('>>> ' + seg)
        out.append('---')

# 另找 in_progress:!0 附近
for m in re.finditer(r'in_progress:!0', JS):
    i = m.start()
    seg = JS[max(0, i-500):i+400].replace('\n', ' ')
    out.append('>>>IP ' + seg)
    out.append('---')

# 找 user_vote_limit / page_node_id 字段
for kw in ['user_vote_limit', 'page_node_id', 'allow_other_users_to_add']:
    idxs = [m.start() for m in re.finditer(re.escape(kw), JS)]
    out.append('===== %s :: %d =====' % (kw, len(idxs)))
    for i in idxs[:8]:
        seg = JS[max(0, i-300):i+300].replace('\n', ' ')
        out.append('>>> ' + seg)
        out.append('---')

io.open(os.path.join(d, '_r209m_votebody_out.txt'), 'w', encoding='utf-8').write('\n'.join(out))
print('DONE lines:', len(out))

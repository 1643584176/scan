# -*- coding: utf-8 -*-
# r209d: canvas_mentions 调用点 + in_context asset_keys 格式 + library status key 语义
import io, re, os
d = os.path.dirname(os.path.abspath(__file__))
JS = io.open(os.path.join(d, '_js/figma_app-main.js'), encoding='utf-8', errors='replace').read()

out = []
for kw in ['mentionedUserId', 'mentioned_user_id', 'getCanvasMentionsFileNeedsInvite',
           'getInContextPublishedComponents', 'asset_keys', 'assetKeys',
           'getLibraryIngestionStatus', 'ingestion_status', 'needs_invite',
           'shouldAddUserGroupToFile', 'recordCanvasMention']:
    idxs = [m.start() for m in re.finditer(re.escape(kw), JS)]
    out.append('===== %s :: %d hits =====' % (kw, len(idxs)))
    for i in idxs[:20]:
        seg = JS[max(0, i-250):i+400].replace('\n', ' ')
        out.append('  >>> ' + seg)
        out.append('  ---')
    out.append('')

io.open(os.path.join(d, '_r209d_callers_out.txt'), 'w', encoding='utf-8').write('\n'.join(out))
print('DONE lines:', len(out))

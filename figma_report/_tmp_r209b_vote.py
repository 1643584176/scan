# -*- coding: utf-8 -*-
# r209b: voting_sessions POST body (requestBody) 构造点深挖
import io, re, os
d = os.path.dirname(os.path.abspath(__file__))
JS = io.open(os.path.join(d, '_js/figma_app-main.js'), encoding='utf-8', errors='replace').read()

out = []
for kw in ['requestBody', 'votingSession', 'voting_session', 'VotingSession', 'createVotingSession', 'start_voting_session', 'addedVotes', 'PollVote', 'voting']:
    idxs = [m.start() for m in re.finditer(re.escape(kw), JS)]
    out.append('===== %s :: %d hits =====' % (kw, len(idxs)))
    for i in idxs[:30]:
        seg = JS[max(0, i-200):i+400].replace('\n', ' ')
        out.append('  >>> ' + seg)
        out.append('  ---')
    out.append('')

io.open(os.path.join(d, '_r209b_vote_out.txt'), 'w', encoding='utf-8').write('\n'.join(out))
print('DONE lines:', len(out))

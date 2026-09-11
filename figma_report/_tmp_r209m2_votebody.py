# -*- coding: utf-8 -*-
# r209m2: 跨 chunk 搜 voting requestBody 调用方
import io, re, os, glob
d = os.path.dirname(os.path.abspath(__file__))
files = [os.path.join(d, '_js/figma_app-main.js')] + sorted(glob.glob(os.path.join(d, '_js/*.min.js')))
out = []
pats = [r'requestBody\s*[:=]', r'startVotingSession', r'voting_sessions', r'vote_limit', r'voteLimit', r'VotingSessionInput', r'create_voting']
for fp in files:
    base = os.path.basename(fp)
    JS = io.open(fp, encoding='utf-8', errors='replace').read()
    for pat in pats:
        idxs = [m.start() for m in re.finditer(pat, JS)]
        if not idxs:
            continue
        out.append('##### %s :: %s :: %d hits' % (base, pat, len(idxs)))
        for i in idxs[:6]:
            seg = JS[max(0, i-350):i+450].replace('\n', ' ')
            out.append('  >>> ' + seg)
            out.append('  ---')

io.open(os.path.join(d, '_r209m2_votebody_out.txt'), 'w', encoding='utf-8').write('\n'.join(out))
print('DONE lines:', len(out))

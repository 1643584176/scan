# -*- coding: utf-8 -*-
import io, re, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
ls = [l[3:].strip() for l in open(r'D:\scan\_tmp_untracked_all.txt', encoding='utf-8', errors='replace') if l.startswith('?? ')]
pat = re.compile(r'(creds?|credential|apikey|api[_-]?key|secret|passwd|password|pwd|\.pem$|\.key$|\.har$|token|cookie|session|jwt|\.pfx$|\.p12$|auth)', re.I)
out = []
for p in ls:
    base = p.split('/')[-1].lower()
    if pat.search(base):
        out.append(p)
print('\n'.join(out) if out else 'NO MATCH')
print('TOTAL', len(out))

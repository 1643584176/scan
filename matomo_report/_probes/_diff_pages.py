# -*- coding: utf-8 -*-
"""Diff failed-POST page vs plain welcome page to find real rendering."""
import difflib

a = open(r'F:\scan\matomo_report\_probes\_install_0.html', encoding='utf-8', errors='replace').read()
b = open(r'F:\scan\matomo_report\_probes\_site_post.html', encoding='utf-8', errors='replace').read()
print('len a', len(a), 'len b', len(b))

sm = difflib.SequenceMatcher(None, a, b)
opcodes = [o for o in sm.get_opcodes() if o[0] != 'equal']
print('diff blocks:', len(opcodes))
for tag, i1, i2, j1, j2 in opcodes[:12]:
    if tag == 'replace':
        print('REPLACE a[%d:%d]: %r' % (i1, i2, a[i1:i1 + 300]))
        print('     -> b[%d:%d]: %r' % (j1, j2, b[j1:j1 + 300]))
    elif tag == 'delete':
        print('DELETE a[%d:%d]: %r' % (i1, i2, a[i1:i1 + 300]))
    else:
        print('INSERT b[%d:%d]: %r' % (j1, j2, b[j1:j1 + 300]))

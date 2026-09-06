# -*- coding: utf-8 -*-
import json
import re
from collections import Counter

d = json.load(open('_nocheck_methods.json', encoding='utf-8'))
callable_ = [x for x in d if not x['method'].startswith('_')]
print('total:', len(d), 'callable(not _*):', len(callable_))

by_plugin = Counter(x['file'].split('\\')[-2] for x in callable_)
print('by plugin:', dict(by_plugin))

has_id = []
for x in callable_:
    names = re.findall(r'\$(\w+)', x['params'])
    if any(n in ('idSite', 'idSites', 'siteId', 'idUser', 'userLogin', 'token_auth') for n in names):
        has_id.append((x['file'].split('\\')[-2], x['method'], names))
print('methods with id-ish params:', len(has_id))
for p, m, n in has_id:
    print('  %-25s %-50s %s' % (p, m, n))

# methods with zero params (callable bare)
zero = [x for x in callable_ if not re.findall(r'\$(\w+)', x['params'])]
print('zero-param methods:', len(zero))
for x in zero:
    print('  %-25s %s' % (x['file'].split('\\')[-2], x['method']))

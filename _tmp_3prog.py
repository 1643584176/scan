# -*- coding: utf-8 -*-
import os
import sys

os.chdir(r'F:\scan')
sys.path.insert(0, r'F:\scan')
from h1kit import h1data

for h in ['faraday_inc', 'mergify', 'matomo']:
    info = h1data.program_info(h)
    if not info:
        print(h, 'NOT FOUND')
        continue
    print('=' * 100)
    print('==', info['name'], '|', info['url'], '| bounties:', info['offers_bounties'])
    for tag in ('in_scope', 'out_of_scope'):
        lst = info[tag]
        print('--- %s (%d) ---' % (tag, len(lst)))
        for t in lst:
            print('*', t.get('asset_identifier'), '|', t.get('asset_type'),
                  '| bounty:', t.get('eligible_for_bounty'))
            ins = (t.get('instruction') or '').strip()
            if ins:
                print('    ', ins[:400].replace('\n', ' '))

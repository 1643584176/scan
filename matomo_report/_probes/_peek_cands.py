# -*- coding: utf-8 -*-
import json

d = json.load(open('_mt06_mgmt_matrix.json', encoding='utf-8'))
targets = {'getBulkRequest', 'getFollowingPages', 'getIpsForRange', 'getSettings',
           'getPagesComparisonsDisabledFor', 'getTranslationsForLanguage'}
for r in d:
    if r['method'] in targets:
        print('=' * 100)
        print('%s.%s kind=%s' % (r['plugin'], r['method'], r['kind']))
        for who in ('admin', 'user2', 'user3'):
            b = r.get(who + '_body', '')
            print('--- %s [%s] %s' % (who, r[who], b[:400]))

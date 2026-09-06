# -*- coding: utf-8 -*-
"""FULL report-layer matrix for closure: all no-check report methods
(REPORT_PLUGINS) x admin/user2/user3 x idSite 1(foreign)/2(own).
Flags any role-site combo that is NOT denied for foreign/zero-access users."""
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request

BASE = 'http://127.0.0.1:8080/'
TOKENS = {
    'admin': 'c3bf071d7f0db740a6f4c60c6affcfd5',
    'user2': '794beeb243443742f0df05b4432c734e',
    'user3': 'bfb52eb146d39b0d40c365a46491f589',
}
REPORT_PLUGINS = {'Contents', 'CustomDimensions', 'DevicePlugins', 'DevicesDetection',
                  'Events', 'Goals', 'Referrers', 'Resolution', 'Transitions',
                  'UserCountry', 'UserLanguage', 'VisitorInterest', 'VisitsSummary',
                  'VisitTime', 'Actions'}


def api(tok, method, extra, timeout=60):
    q = dict(extra, module='API', method=method, format='json', period='day',
             date='today')
    if tok:
        q['token_auth'] = tok
    url = BASE + 'index.php?' + urllib.parse.urlencode(q)
    req = urllib.request.Request(url)
    try:
        r = urllib.request.urlopen(req, timeout=timeout)
        return r.status, r.read().decode('utf-8', 'replace')
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode('utf-8', 'replace')
    except Exception as e:
        return 'ERR', str(e)[:120]


def classify(s, b):
    try:
        j = json.loads(b)
    except Exception:
        return 'NONJSON:%s' % s
    if isinstance(j, dict) and j.get('result') == 'error':
        msg = j.get('message', '')
        low = msg.lower()
        if 'view' in low and 'access' in low:
            return 'DENIED-view'
        if 'admin' in low or 'super user' in low:
            return 'DENIED-admin'
        if 'does not exist' in msg:
            return 'NOT_AVAIL'
        if 'please specify' in low or 'period' in low or 'date' in low:
            return 'PARAM_ERR'
        if 'no data' in low:
            return 'ERR-noData'
        return 'ERR:' + msg[:60]
    if isinstance(j, dict) and 'value' in j:
        return 'DATA-val'
    if isinstance(j, list):
        return 'DATA-list'
    if isinstance(j, dict) and j:
        return 'DATA-map'
    return 'DATA-empty'


def main():
    entries = json.load(open('_nocheck_methods.json', encoding='utf-8'))
    callable_ = [x for x in entries if not x['method'].startswith('_')]
    methods = [x for x in callable_ if x['file'].split('\\')[-2] in REPORT_PLUGINS]
    print('report no-check methods:', len(methods))
    # strip already-tested sample (mt06_report_probe) -> full rerun is fine, keep all

    flags = []
    rows = []
    t0 = time.time()
    for i, x in enumerate(methods):
        plugin = x['file'].split('\\')[-2]
        for idsite in ('1', '2'):
            row = {'plugin': plugin, 'method': x['method'], 'idsite': idsite}
            # required params from signature (rough): fill idSite/period/date; others from known map
            for who in ('admin', 'user2', 'user3'):
                extra = {'idSite': idsite}
                if plugin == 'Transitions':
                    extra.update({'pageUrl': 'http://127.0.0.1:8080/home',
                                  'pageTitle': 'Home'})
                if plugin == 'CustomDimensions':
                    extra.update({'scope': 'visit'})
                if x['method'] in ('Events.getActionFromCategoryId', 'Events.getNameFromCategoryId',
                                   'Events.getCategoryFromActionId', 'Events.getNameFromActionId',
                                   'Events.getActionFromNameId', 'Events.getCategoryFromNameId'):
                    extra.update({'idSubtable': '1'})
                if x['method'] in ('Goals.getConversions', 'Goals.getNbVisitsConverted',
                                   'Goals.getConversionRate', 'Goals.getRevenue',
                                   'Goals.getDaysToConversion', 'Goals.getVisitsUntilConversion'):
                    extra.update({'idGoal': '1'})
                if x['method'] in ('Goals.getItemsSku', 'Goals.getItemsName', 'Goals.getItemsCategory'):
                    extra.update({'abandonedCarts': '0'})
                if x['method'] in ('Overlay.getExcludedQueryParameters',):
                    pass
                s, b = api(TOKENS[who], plugin + '.' + x['method'], extra)
                cls = classify(s, b)
                row[who] = cls
            # flag: foreign/zero user NOT denied on a method where admin got data
            bad = []
            if row['user3'] not in ('DENIED-view', 'DENIED-admin', 'NOT_AVAIL', 'PARAM_ERR'):
                bad.append('user3=' + row['user3'])
            if idsite == '1' and row['user2'] not in ('DENIED-view', 'DENIED-admin', 'NOT_AVAIL', 'PARAM_ERR'):
                bad.append('user2=' + row['user2'])
            if row['admin'].startswith('DATA') and bad:
                row['FLAG'] = ';'.join(bad)
                flags.append(row)
            rows.append(row)
            print('%3d/%-3d %-18s %-44s idS=%s admin=%-12s u2=%-12s u3=%-12s %s'
                  % (i + 1, len(methods), plugin, x['method'][:42], idsite,
                     row['admin'][:10], row['user2'][:10], row['user3'][:10],
                     row.get('FLAG', '')))
        if (i + 1) % 10 == 0:
            print('... %d/%d done, %.0fs elapsed' % (i + 1, len(methods), time.time() - t0))

    json.dump(rows, open('_mt06_report_full.json', 'w', encoding='utf-8'),
              indent=1, ensure_ascii=False)
    print('TOTAL rows:', len(rows), 'FLAGGED:', len(flags))
    for f in flags:
        print('FLAG %s.%s idS=%s %s' % (f['plugin'], f['method'], f['idsite'], f['FLAG']))


if __name__ == '__main__':
    main()

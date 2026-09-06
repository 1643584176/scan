# -*- coding: utf-8 -*-
"""Verify archived baseline numbers for admin (site1 vs site2)."""
import json
import urllib.error
import urllib.parse
import urllib.request

TOK = 'c3bf071d7f0db740a6f4c60c6affcfd5'


def api(method, timeout=60, **params):
    q = urllib.parse.urlencode(dict(params, module='API', method=method,
                                    format='json', token_auth=TOK))
    req = urllib.request.Request('http://127.0.0.1:8080/index.php?' + q)
    try:
        r = urllib.request.urlopen(req, timeout=timeout)
        return r.status, json.loads(r.read().decode('utf-8', 'replace'))
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode('utf-8', 'replace')[:300]


def flat(d, depth=0):
    if isinstance(d, dict):
        if 'label' in d or 'value' in d or 'idsubdatatable' in d:
            keep = {k: v for k, v in d.items()
                    if k in ('label', 'value', 'nb_visits', 'nb_uniq_visitors',
                             'nb_actions', 'nb_events', 'nb_conversions', 'revenue',
                             'sum_visit_length', 'bounce_count', 'nb_visits_converted',
                             'nb_users', 'max_actions', 'idsubdatatable')}
            return [keep]
        out = []
        for v in d.values():
            out += flat(v, depth + 1)
        return out
    if isinstance(d, list):
        out = []
        for v in d:
            out += flat(v, depth + 1)
        return out
    return []


for idsite in (1, 2):
    print('=' * 30, 'site', idsite)
    for m in ['VisitsSummary.getVisits', 'VisitsSummary.getActions',
              'Actions.getPageUrls', 'Events.getAction', 'DevicesDetection.getType',
              'UserCountry.getCountry', 'Goals.getGoals', 'Goals.get']:
        s, b = api(m, idSite=idsite, period='day', date='today', flat='1')
        rows = flat(b)
        print('%-32s %s -> %s' % (m, s, json.dumps(rows[:6], ensure_ascii=False)[:300]))

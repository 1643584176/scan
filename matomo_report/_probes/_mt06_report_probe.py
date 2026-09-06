# -*- coding: utf-8 -*-
"""Probe report-layer methods with user3(no rights)/user2(site2 view only) on
idSite=1 foreign + idSite=2 own; admin baseline. Determine if a public check layer
guards no-check report methods."""
import json
import urllib.error
import urllib.parse
import urllib.request

BASE = 'http://127.0.0.1:8080/'
TOKENS = {
    'admin': 'c3bf071d7f0db740a6f4c60c6affcfd5',
    'user2': '794beeb243443742f0df05b4432c734e',
    'user3': 'bfb52eb146d39b0d40c365a46491f589',
}

METHODS = [
    ('VisitsSummary.getVisits', {}),
    ('Events.getAction', {}),
    ('Events.getCategory', {}),
    ('DevicesDetection.getType', {}),
    ('UserCountry.getCountry', {}),
    ('Referrers.getNumberOfDistinctSearchEngines', {}),
    ('Goals.getConversions', {}),
    ('Contents.getContentNames', {}),
    ('CustomDimensions.getConfiguredCustomDimensionsHavingScope', {'scope': 'visit'}),
    ('Transitions.getTransitionsForPageUrl', {'pageUrl': 'http://127.0.0.1:8080/home'}),
    ('VisitorInterest.getNumberOfVisitsPerVisitDuration', {}),
    ('VisitTime.getVisitInformationPerServerTime', {}),
    ('Resolution.getConfiguration', {}),
    ('DevicePlugins.getPlugin', {}),
]


def api(tok, method, extra, timeout=45):
    q = dict(extra, module='API', method=method, format='json', period='day',
             date='today')
    if tok:
        q['token_auth'] = tok
    if method == 'CustomDimensions.getConfiguredCustomDimensionsHavingScope':
        q.pop('period', None)
        q.pop('date', None)
    url = BASE + 'index.php?' + urllib.parse.urlencode(q)
    req = urllib.request.Request(url)
    try:
        r = urllib.request.urlopen(req, timeout=timeout)
        return r.status, r.read().decode('utf-8', 'replace')
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode('utf-8', 'replace')
    except Exception as e:
        return 'ERR', str(e)[:120]


print('%-64s %-9s %-24s %-24s %-24s' % ('method', 'idSite', 'admin', 'user2', 'user3'))
for m, extra in METHODS:
    for idsite, label in (('1', 'idS=1'), ('2', 'idS=2')):
        row = []
        for who in ('admin', 'user2', 'user3'):
            s, b = api(TOKENS[who], m, dict(extra, idSite=idsite))
            try:
                j = json.loads(b)
                if isinstance(j, dict) and j.get('result') == 'error':
                    msg = j.get('message', '')
                    if 'view' in msg and 'access' in msg:
                        cls = 'DENIED(view)'
                    elif 'admin' in msg or 'super user' in msg:
                        cls = 'DENIED(admin)'
                    elif 'does not exist' in msg:
                        cls = 'NOT_AVAIL'
                    elif 'Please specify' in msg or 'period' in msg.lower() or 'date' in msg.lower():
                        cls = 'PARAM'
                    else:
                        cls = 'ERR:' + msg[:40]
                elif isinstance(j, dict) and 'value' in j:
                    cls = 'DATA val=%s' % j['value']
                elif isinstance(j, list):
                    cls = 'DATA rows=%d' % len(j)
                else:
                    cls = 'DATA %s' % str(j)[:50]
            except Exception:
                cls = 'HTTP%s' % s
            row.append(cls[:23])
        print('%-45s %-6s %-24s %-24s %-24s' % (m + extra.get('scope', ''), label, row[0], row[1], row[2]))

# -*- coding: utf-8 -*-
"""Check API responds fast now (no archiving self-deadlock)."""
import json
import time
import urllib.error
import urllib.parse
import urllib.request

TOK = 'c3bf071d7f0db740a6f4c60c6affcfd5'


def api(method, timeout=30, **params):
    q = urllib.parse.urlencode(dict(params, module='API', method=method,
                                    format='json', token_auth=TOK))
    req = urllib.request.Request('http://127.0.0.1:8080/index.php?' + q)
    t0 = time.time()
    try:
        r = urllib.request.urlopen(req, timeout=timeout)
        body = r.read().decode('utf-8', 'replace')
        return r.status, round(time.time() - t0, 2), body[:200]
    except urllib.error.HTTPError as e:
        return e.code, round(time.time() - t0, 2), e.read().decode('utf-8', 'replace')[:200]
    except Exception as e:
        return 'ERR', round(time.time() - t0, 2), str(e)[:150]


for m, kw in [('VisitsSummary.getVisits', dict(idSite=1, period='day', date='today')),
              ('Goals.getGoals', dict(idSite=1)),
              ('SitesManager.getSiteFromId', dict(idSite=1))]:
    s, t, b = api(m, **kw)
    print('%s | %s | %.2fs | %s' % (m, s, t, b.replace('\n', ' ')[:180]))

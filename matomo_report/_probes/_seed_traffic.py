# -*- coding: utf-8 -*-
"""Seed traffic into site1 + site2 via matomo.php tracker; create a goal on site1 first."""
import json
import random
import time
import urllib.error
import urllib.parse
import urllib.request

BASE = 'http://127.0.0.1:8080/'
TOK = 'c3bf071d7f0db740a6f4c60c6affcfd5'


def api(method, **params):
    q = urllib.parse.urlencode(dict(params, module='API', method=method,
                                    format='json', token_auth=TOK))
    req = urllib.request.Request(BASE + 'index.php?' + q)
    try:
        r = urllib.request.urlopen(req, timeout=120)
        return json.loads(r.read().decode('utf-8', 'replace'))
    except urllib.error.HTTPError as e:
        return {'http_error': e.code, 'body': e.read().decode('utf-8', 'replace')[:300]}


def track(idsite, url, name, ua, uid=None, events=None, goal=None, ts=None):
    p = {'idsite': idsite, 'rec': '1', 'url': url, 'action_name': name,
         '_id': '%016x' % random.getrandbits(64), 'rand': '%08x' % random.getrandbits(32)}
    if uid:
        p['uid'] = uid
    if events:
        for i, (c, a, n) in enumerate(events):
            p['e_c' + (str(i) if i else '')] = c
            p['e_a' + (str(i) if i else '')] = a
            if n:
                p['e_n' + (str(i) if i else '')] = n
    if goal:
        p['idgoal'] = goal
    if ts:
        p['cdt'] = ts
    data = urllib.parse.urlencode(p).encode()
    req = urllib.request.Request(BASE + 'matomo.php', data=data)
    req.add_header('User-Agent', ua)
    req.add_header('X-Forwarded-For', '203.0.113.%d' % random.randint(2, 250))
    try:
        r = urllib.request.urlopen(req, timeout=60)
        return r.status
    except urllib.error.HTTPError as e:
        return 'HTTP%d %s' % (e.code, e.read().decode('utf-8', 'replace')[:200])


# 1) goal on site1 (url contains /thankyou) + on site2
r = api('Goals.addGoal', idSite=1, name='Buy S1', matchAttribute='url',
        pattern='thankyou', patternType='contains')
print('goal s1:', r)
r = api('Goals.addGoal', idSite=2, name='Buy S2', matchAttribute='url',
        pattern='thankyou', patternType='contains')
print('goal s2:', r)

# 2) site1 traffic: 3 visitors, distinct UA + pages, one conversion w/ revenue
UA1 = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0 Safari/537.36'
UA2 = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15'
UA3 = 'Mozilla/5.0 (X11; Linux x86_64; rv:126.0) Gecko/20100101 Firefox/126.0'
print('s1 t1:', track(1, 'http://127.0.0.1:8080/home', 'Home', UA1, uid='vis-a',
                      events=[('Product', 'View', 'widget'), ('Product', 'AddToCart', None)]))
print('s1 t2:', track(1, 'http://127.0.0.1:8080/about', 'About', UA2, uid='vis-b',
                      events=[('Product', 'View', 'gadget')]))
print('s1 t3:', track(1, 'http://127.0.0.1:8080/thankyou', 'ThankYou', UA3, uid='vis-c',
                      goal='1'))
# revenue via order goal variant would need ecommerce; skip

# 3) site2 traffic: 2 visitors, Edge + distinct pages
UA4 = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36 Edg/126.0'
UA5 = 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 Version/17.5 Mobile/15E148 Safari/604.1'
print('s2 t1:', track(2, 'http://site2.local/s2a', 'S2 A', UA4, uid='s2-user-x'))
print('s2 t2:', track(2, 'http://site2.local/s2b/thankyou', 'S2 B', UA5, uid='s2-user-y', goal='1'))

# 4) wait for archiving & verify admin can read
time.sleep(4)
for m in ['VisitsSummary.getVisits', 'Events.getAction', 'DevicesDetection.getType',
          'UserCountry.getCountry']:
    r = api(m, idSite=1, period='day', date='today')
    print('admin', m, str(r)[:180])
r = api('VisitsSummary.getVisits', idSite=2, period='day', date='today')
print('admin site2 getVisits:', str(r)[:180])

# 5) trigger archiving explicitly via API (browser archiving disabled locally -> no self-http)
for m in ['VisitsSummary.getVisits', 'Goals.getConversions']:
    r = api(m, idSite='all', period='day', date='today')
    print('archive-warm', m, str(r)[:120])

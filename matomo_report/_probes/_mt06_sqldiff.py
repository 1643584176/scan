# -*- coding: utf-8 -*-
"""SQL scope diff prep: truncate general log, run SAME request as admin/user2/user3
(VisitsSummary.getVisits idSite=1 & Events.getAction idSite=2), then dump the SQL
each role actually executed. Uses PHP CLI to clear + tail log file via python."""
import time
import urllib.error
import urllib.parse
import urllib.request

BASE = 'http://127.0.0.1:8080/'
GLOG = r'F:\scan\matomo_report\_runtime\mariadb\matomo_general.log'
TOKENS = {
    'admin': 'c3bf071d7f0db740a6f4c60c6affcfd5',
    'user2': '794beeb243443742f0df05b4432c734e',
    'user3': 'bfb52eb146d39b0d40c365a46491f589',
}


def api(tok, method, extra, timeout=150):
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


def clear_log():
    """SET GLOBAL general_log = OFF; TRUNCATE the table? general log to file can't be
    truncated via SQL; instead mark current file size."""
    with open(GLOG, 'rb') as f:
        f.seek(0, 2)
        return f.tell()


def tail_log(pos):
    with open(GLOG, 'rb') as f:
        f.seek(pos)
        return f.read().decode('utf-8', 'replace')


# mark current end
pos = clear_log()
print('log start offset:', pos)

CASES = [
    ('admin', 'VisitsSummary.getVisits', {'idSite': '1'}),
    ('user3', 'VisitsSummary.getVisits', {'idSite': '1'}),
    ('user2', 'VisitsSummary.getVisits', {'idSite': '1'}),
    ('user2', 'VisitsSummary.getVisits', {'idSite': '2'}),
    ('user3', 'Events.getAction', {'idSite': '2'}),
    ('user2', 'Events.getAction', {'idSite': '2'}),
]
for who, m, extra in CASES:
    s, b = api(TOKENS[who], m, extra)
    print('--- %s %s %s -> %s' % (who, m, extra, s))

time.sleep(1)
log = tail_log(pos)
print('=' * 80)
print('SQL statements executed (tail %d bytes):' % len(log))
print(log[:6000])

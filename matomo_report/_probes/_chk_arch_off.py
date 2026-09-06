# -*- coding: utf-8 -*-
"""Check if API request still triggers archiving SQL (general log growth check)."""
import time
import urllib.error
import urllib.parse
import urllib.request

GLOG = r'F:\scan\matomo_report\_runtime\mariadb\matomo_general.log'


def size():
    with open(GLOG, 'rb') as f:
        f.seek(0, 2)
        return f.tell()


def tail_since(pos):
    with open(GLOG, 'rb') as f:
        f.seek(pos)
        return f.read().decode('utf-8', 'replace')


pos = size()
print('start offset:', pos)
q = urllib.parse.urlencode({'module': 'API', 'method': 'VisitsSummary.getVisits',
                            'idSite': '1', 'period': 'day', 'date': 'today',
                            'format': 'json', 'token_auth': 'c3bf071d7f0db740a6f4c60c6affcfd5'})
t0 = time.time()
r = urllib.request.urlopen('http://127.0.0.1:8080/index.php?' + q, timeout=90)
print('resp %.1fs: %s' % (time.time() - t0, r.read().decode('utf-8', 'replace')[:100]))
time.sleep(1)
log = tail_since(pos)
arch = [l for l in log.splitlines() if 'case when' in l or 'ArchiveWriter' in l or 'archive' in l.lower()]
print('log growth: %d bytes, %d lines, archiving-ish lines: %d' % (len(log), len(log.splitlines()), len(arch)))
for l in log.splitlines()[:20]:
    print(l.strip()[:160])

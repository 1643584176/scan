# -*- coding: utf-8 -*-
"""Second fast request + check for archive-table writes."""
import time
import urllib.error
import urllib.parse
import urllib.request

GLOG = r'F:\scan\matomo_report\_runtime\mariadb\matomo_general.log'


def size():
    with open(GLOG, 'rb') as f:
        f.seek(0, 2)
        return f.tell()


pos = size()
q = urllib.parse.urlencode({'module': 'API', 'method': 'VisitsSummary.getVisits',
                            'idSite': '1', 'period': 'day', 'date': 'today',
                            'format': 'json', 'token_auth': 'c3bf071d7f0db740a6f4c60c6affcfd5'})
t0 = time.time()
r = urllib.request.urlopen('http://127.0.0.1:8080/index.php?' + q, timeout=90)
print('resp %.1fs' % (time.time() - t0))
time.sleep(1)
with open(GLOG, 'rb') as f:
    f.seek(pos)
    log = f.read().decode('utf-8', 'replace')
writes = [l.strip()[:200] for l in log.splitlines()
          if 'INSERT INTO' in l and 'archive' in l.lower()]
print('archive INSERT lines:', len(writes))
for w in writes[:8]:
    print(w)

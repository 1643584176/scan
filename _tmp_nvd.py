# -*- coding: utf-8 -*-
"""Pull Matomo CVEs from NVD API v2."""
import json
import urllib.request

url = ('https://services.nvd.nist.gov/rest/json/cves/2.0?'
       'keywordSearch=matomo&resultsPerPage=200')
req = urllib.request.Request(url, headers={'User-Agent': 'h1kit/1.0'})
with urllib.request.urlopen(req, timeout=60) as r:
    d = json.load(r)

items = d.get('vulnerabilities') or []
print('total:', d.get('totalResults'))
for it in sorted(items, key=lambda x: x['cve']['published']):
    c = it['cve']
    cid = c['id']
    desc = next((x['value'] for x in c['descriptions'] if x['lang'] == 'en'), '')
    sev = ''
    for m in c.get('metrics', {}).values():
        for s in m:
            sev = s.get('baseSeverity', '')
            break
        if sev:
            break
    print('%s | %-6s | %s | %s' % (cid, sev, c['published'][:10], desc[:150].replace('\n', ' ')))

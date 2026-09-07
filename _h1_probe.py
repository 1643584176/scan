# -*- coding: utf-8 -*-
"""H1 hacktivity/报告页 SSR 探测: 普通UA vs Googlebot UA (2 req)"""
import urllib.request, ssl, sys

URLS = [
    'https://hackerone.com/hacktivity/overview?queryString=disclosed%3Atrue&sortField=latest_disclosable_activity_at&sortDirection=DESC&pageIndex=0',
]
UAS = {
    'chrome': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36',
    'googlebot': 'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)',
    'bingbot': 'Mozilla/5.0 (compatible; bingbot/2.0; +http://www.bing.com/bingbot.htm)',
}
ctx = ssl.create_default_context()

for name, ua in UAS.items():
    try:
        r = urllib.request.Request(URLS[0], headers={'User-Agent': ua, 'Accept': 'text/html,application/xhtml+xml'})
        resp = urllib.request.urlopen(r, timeout=15, context=ctx)
        body = resp.read().decode('utf-8', 'replace')
        print('== %-10s -> %d  %d bytes' % (name, resp.status, len(body)))
        # 特征检测
        low = body.lower()
        for marker in ['js-disabled', '__next_data__', 'report', 'hacktivity', 'disclos', 'noscript', 'self.__next']:
            if marker in low:
                idx = low.find(marker)
                print('    marker [%s] @ %d: ...%s...' % (marker, idx, body[max(0, idx-60):idx+120].replace('\n', ' ')[:200]))
    except Exception as e:
        print('== %-10s -> ERR %s' % (name, e))

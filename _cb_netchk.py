# -*- coding: utf-8 -*-
import requests, time
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
s = requests.Session(); s.headers['User-Agent'] = UA
for name, url, t in [
    ('baidu-ctrl', 'https://www.baidu.com/', 10),
    ('api-vercel-ctrl', 'https://api.vercel.com/v2/teams', 10),
    ('coinbase-www', 'https://www.coinbase.com/', 15),
    ('coinbase-api', 'https://api.coinbase.com/v2/time', 15),
    ('coinbase-robots', 'https://www.coinbase.com/robots.txt', 10),
]:
    try:
        r = s.get(url, timeout=t, allow_redirects=False)
        print('[%s] HTTP %d | %dB' % (name, r.status_code, len(r.content)), flush=True)
    except Exception as e:
        print('[%s] ERROR %s' % (name, str(e)[:120]), flush=True)
    time.sleep(1)

# -*- coding: utf-8 -*-
"""Coinbase 匿名面探测 v1:公开端点只读 GET(规则内,无账号无写操作)"""
import requests, time, sys

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
s = requests.Session()
s.headers['User-Agent'] = UA

def probe(name, url, timeout=20):
    try:
        r = s.get(url, timeout=timeout, allow_redirects=False)
        body = r.text[:400].replace('\n', ' ')
        print('[%s] %s -> HTTP %d | %dB | CT=%s' % (name, url, r.status_code, len(r.content), r.headers.get('content-type','')), flush=True)
        print('   body: %s' % body, flush=True)
        return r
    except Exception as e:
        print('[%s] %s -> ERROR %s' % (name, url, e), flush=True)
        return None

print('== api.coinbase.com 公开端点 ==', flush=True)
probe('time', 'https://api.coinbase.com/v2/time')
time.sleep(1.2)
probe('prices', 'https://api.coinbase.com/v2/prices/BTC-USD/spot')
time.sleep(1.2)
probe('currencies', 'https://api.coinbase.com/v2/currencies')
time.sleep(1.2)
probe('exchange-rates', 'https://api.coinbase.com/v2/exchange-rates')
time.sleep(1.2)
probe('unauth-account', 'https://api.coinbase.com/v2/accounts')
time.sleep(1.2)
probe('unauth-user', 'https://api.coinbase.com/v2/user')
time.sleep(1.2)
print('== www.coinbase.com ==', flush=True)
probe('home', 'https://www.coinbase.com/')
time.sleep(1.5)
probe('robots', 'https://www.coinbase.com/robots.txt')
time.sleep(1.2)
probe('security', 'https://www.coinbase.com/.well-known/security.txt')

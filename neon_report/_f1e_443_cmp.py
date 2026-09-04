# -*- coding: utf-8 -*-
"""对照:ep-* proxy 域 443 vs br-* compute/storage 域 443 —— 判断 Beta 数据面是否整体锁"""
import http.client, ssl
ctx = ssl.create_default_context()
for host in ('ep-crimson-fog-w2gucld1.us-east-2.aws.neon.build',          # pg proxy(通)
             'br-wandering-field-w2ob6mpn-kf1.compute.c-1.us-east-2.aws.neon.build',  # function
             'br-wandering-field-w2ob6mpn.storage.c-1.us-east-2.aws.neon.build',      # storage
             'us-east-2.aws.neon.build'):                                              # 泛域
    try:
        c = http.client.HTTPSConnection(host, context=ctx, timeout=15)
        c.request('GET', '/', headers={'User-Agent': 'Mozilla/5.0'})
        r = c.getresponse(); raw = r.read(); hdrs = dict(r.getheaders()); c.close()
        print('%-70s -> %d | server: %s | body: %s' % (host, r.status, hdrs.get('Server'), raw[:60]))
    except Exception as e:
        print('%-70s -> ERR %s' % (host, str(e)[:100]))

# -*- coding: utf-8 -*-
"""webhook.site token 创建 + 请求查询"""
import urllib.request, json, sys, time

def log(s): print(s, flush=True)

def http(method, url, body=None, timeout=15):
    req = urllib.request.Request(url, data=body, method=method)
    req.add_header('Content-Type', 'application/json')
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()
    except Exception as e:
        return -1, str(e).encode()

if __name__ == '__main__':
    c, r = http('POST', 'https://webhook.site/token', b'{}')
    log('create -> %d %r' % (c, r[:200]))
    if c == 201 or c == 200:
        d = json.loads(r)
        uuid = d.get('uuid')
        log('uuid=%s' % uuid)
        open('_wh_uuid.txt', 'w').write(uuid)
        # 等 3s 再查一次空请求列表确认 API 工作
        time.sleep(3)
        c2, r2 = http('GET', 'https://webhook.site/token/%s/requests' % uuid)
        log('list -> %d %r' % (c2, r2[:300]))

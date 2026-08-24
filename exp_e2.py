# 实验E2: 连接级(keep-alive)注入边界 + 直通确认
# 复用 expe1 沙箱: update allow: httpbin.org -> [{match:{path:{exact:"/anything"}}, forwardURL:"https://httpbin.org/anything"}]
# 1) 新连接 GET /ip        -> 不匹配 -> 确认直通原目标(200 + 无 Vercel 头)
# 2) keep-alive: /anything 匹配转发 -> 同连接 /ip 不匹配 -> 观察是否也被转发(连接级规则?)
# 3) keep-alive: /ip 先 -> /anything 后
# 4) 捕获 HTTPError 的 body 判断 404 归属(httpbin 的 404 有特征 HTML)
import http.client, ssl, json, urllib.error, urllib.request

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def show(label, r, body):
    h = r.getheaders()
    vf = {k: v for k, v in h if k.lower().startswith("vercel-")}
    print(f"== {label}: status={r.status} fwd={list(vf.keys())}")
    for k, v in vf.items():
        print(f"   {k}: {v[:100]}")
    try:
        d = json.loads(body)
        print("   body.url:", d.get("url"))
    except Exception:
        print("   body[:150]:", body[:150])
    print()

# 1. 新连接直通确认
conn = http.client.HTTPSConnection("httpbin.org", 443, context=ctx, timeout=20)
conn.request("GET", "/ip")
r = conn.getresponse()
show("新连接 /ip (不匹配)", r, r.read(1000))
conn.close()

# 2. keep-alive: 匹配 -> 不匹配
conn = http.client.HTTPSConnection("httpbin.org", 443, context=ctx, timeout=20)
conn.request("GET", "/anything")
r1 = conn.getresponse()
b1 = r1.read(1000)
show("连接A[1] /anything (匹配)", r1, b1)
conn.request("GET", "/ip")
r2 = conn.getresponse()
b2 = r2.read(1000)
show("连接A[2] /ip (不匹配,同连接)", r2, b2)
conn.close()

# 3. keep-alive: 不匹配 -> 匹配
conn = http.client.HTTPSConnection("httpbin.org", 443, context=ctx, timeout=20)
conn.request("GET", "/ip")
r3 = conn.getresponse()
b3 = r3.read(1000)
show("连接B[1] /ip (不匹配)", r3, b3)
conn.request("GET", "/anything")
r4 = conn.getresponse()
b4 = r4.read(1000)
show("连接B[2] /anything (匹配,同连接)", r4, b4)
conn.close()

# 4. HTTPError body 判断 404 归属
req = urllib.request.Request("https://httpbin.org/other")
try:
    urllib.request.urlopen(req, context=ctx, timeout=20)
except urllib.error.HTTPError as e:
    body = e.read(300)
    print("== /other HTTPError:", e.code, "server:", e.headers.get("Server"), "body:", body[:200])

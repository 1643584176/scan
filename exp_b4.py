# 实验B4: match method 维度测绘 (policy: match={"method":{"exact":"GET"}})
import urllib.request, urllib.error, json

def req(path, method="GET", custom_headers=None):
    h = dict(custom_headers or {})
    h["User-Agent"] = "exp-b4"
    r = urllib.request.Request(f"https://httpbin.org{path}", headers=h, method=method)
    try:
        with urllib.request.urlopen(r, timeout=12) as resp:
            body = resp.read().decode(errors='replace')
            d = json.loads(body)
            hdrs = d.get("headers", {})
            inj = "X-Test-Inject" in hdrs
            return (f"  {method:<8} {path:<20} -> {resp.status} inj={inj} val={hdrs.get('X-Test-Inject','-')}")
    except urllib.error.HTTPError as e:
        return f"  {method:<8} {path:<20} -> HTTP-{e.code}"
    except Exception as e:
        return f"  {method:<8} {path:<20} -> ERR {type(e).__name__}"

print("== method exact=GET: 方法变体 ==")
for m in ["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS", "get", "Get", "TRACE", "CONNECT"]:
    print(req("/anything", method=m))

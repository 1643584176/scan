# 实验B3: match(path exact=/anything) 绕过测绘
# httpbin /anything 回显所有请求信息(headers/path/query/method)
# 每个变体观察注入头是否出现 -> 判定 matcher 匹配逻辑
import urllib.request, urllib.error, json

def req(path, custom_headers=None, method="GET"):
    h = dict(custom_headers or {})
    h["User-Agent"] = "exp-b3"
    r = urllib.request.Request(f"https://httpbin.org{path}", headers=h, method=method)
    try:
        with urllib.request.urlopen(r, timeout=12) as resp:
            body = resp.read().decode(errors='replace')
            d = json.loads(body)
            hdrs = d.get("headers", {})
            inj = "X-Test-Inject" in hdrs
            return (f"  {method} {path:<28} -> {resp.status} "
                    f"inj={inj} val={hdrs.get('X-Test-Inject','-')} "
                    f"echo_path={d.get('path','?')}")
    except urllib.error.HTTPError as e:
        return f"  {method} {path:<28} -> HTTP-{e.code}"
    except Exception as e:
        return f"  {method} {path:<28} -> ERR {type(e).__name__}:{e}"

print("== [1] path exact=/anything: 路径变体 ==")
for p in ["/anything", "/anything/", "/AnyThing", "/ANYTHING",
          "/anything%2f", "/anything%2F", "/anything?x=1", "/anything?x=/anything",
          "/anything/../anything", "/anything%00", "/./anything", "//anything",
          "/anything/..", "/anything//", "/%61nything", "/anything;foo", "/anything%3f"]:
    print(req(p))

print("== [2] path exact=/anything: 方法变体 ==")
for m in ["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "get", "OPTIONS"]:
    print(req("/anything", method=m))

print("== [3] path exact=/anything: Host/头变体 ==")
print(req("/anything", custom_headers={"X-Test-Inject": "FORGED"}))
print(req("/anything", custom_headers={"x-test-inject": "FORGED-LOWERCASE"}))

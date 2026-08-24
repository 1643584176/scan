# 实验B6: match headers 维度测绘 (policy: match={"headers":{"x-api-key":{"exact":"SECRET"}}})
import urllib.request, urllib.error, json

def req(path, custom_headers=None):
    h = dict(custom_headers or {})
    h["User-Agent"] = "exp-b6"
    r = urllib.request.Request(f"https://httpbin.org{path}", headers=h)
    try:
        with urllib.request.urlopen(r, timeout=12) as resp:
            body = resp.read().decode(errors='replace')
            d = json.loads(body)
            hdrs = d.get("headers", {})
            inj = "X-Test-Inject" in hdrs
            return (f"  {str(custom_headers):<40} -> {resp.status} inj={inj} val={hdrs.get('X-Test-Inject','-')}")
    except urllib.error.HTTPError as e:
        return f"  {str(custom_headers):<40} -> HTTP-{e.code}"
    except Exception as e:
        return f"  {str(custom_headers):<40} -> ERR {type(e).__name__}"

print("== headers x-api-key exact=SECRET ==")
print(req("/anything", {"X-Api-Key": "SECRET"}))
print(req("/anything", {"x-api-key": "SECRET"}))
print(req("/anything", {"X-API-KEY": "SECRET"}))
print(req("/anything", {"X-Api-Key": "secret"}))
print(req("/anything", {"X-Api-Key": "SECRET "}))
print(req("/anything", {"X-Api-Key": " SECRET"}))
print(req("/anything", {"X-Api-Key": "SECRET", "X-Other": "1"}))
print(req("/anything", {"X-Api-Key": "SECRET\x00X"}))
print(req("/anything", {"X-Api-Key": "SECRET\r\nX-Injected: 1"}))
print(req("/anything", {"x-api-key": "SECRET;foo=bar"}))
print(req("/anything", {}))

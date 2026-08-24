# 实验B5: match queryString 维度测绘 (policy: match={"queryString":{"token":{"exact":"SECRET"}}})
import urllib.request, urllib.error, json

def req(path, custom_headers=None):
    h = dict(custom_headers or {})
    h["User-Agent"] = "exp-b5"
    r = urllib.request.Request(f"https://httpbin.org{path}", headers=h)
    try:
        with urllib.request.urlopen(r, timeout=12) as resp:
            body = resp.read().decode(errors='replace')
            d = json.loads(body)
            hdrs = d.get("headers", {})
            inj = "X-Test-Inject" in hdrs
            return (f"  {path:<45} -> {resp.status} inj={inj} val={hdrs.get('X-Test-Inject','-')}")
    except urllib.error.HTTPError as e:
        return f"  {path:<45} -> HTTP-{e.code}"
    except Exception as e:
        return f"  {path:<45} -> ERR {type(e).__name__}"

print("== queryString token exact=SECRET ==")
for p in ["/anything?token=SECRET", "/anything?token=secret", "/anything?Token=SECRET",
          "/anything?token=SECRET&x=1", "/anything?x=1&token=SECRET", "/anything?token=SECRET%20X",
          "/anything?token=SECRET&token=other", "/anything?token=", "/anything?token",
          "/anything?token=SECRET%3d", "/anything?token=SECRET;x=1",
          "/anything?token=%53ECRET", "/anything?TOKEN=SECRET", "/anything?token=SECRET#frag"]:
    print(req(p))

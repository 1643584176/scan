"""Figma 登录态 vs 匿名态 API 对比
从 anon_capture2.json 提取匿名捕获的 GET API，重放为登录态请求，对比响应差异
"""
import json, sys, requests

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE = "https://www.figma.com"
SESSION_FILE = r"D:\scan\_figma_hunt\figma_session.json"

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36")


def load_cookies(path=SESSION_FILE):
    return json.load(open(path, encoding="utf-8"))


def anon_session():
    s = requests.Session()
    s.headers.update({"User-Agent": UA, "Accept": "application/json",
                      "Origin": BASE, "Referer": BASE + "/"})
    return s


def auth_session():
    s = requests.Session()
    for c in load_cookies():
        if c.get("domain") in ("www.figma.com", "figma.com", ".figma.com", ".www.figma.com"):
            s.cookies.set(c["name"], c["value"], domain=c["domain"], path=c.get("path", "/"))
    s.headers.update({"User-Agent": UA, "Accept": "application/json",
                      "Origin": BASE, "Referer": BASE + "/"})
    return s


def summarize(body, limit=220):
    if not body:
        return "(empty)"
    body = body[:limit].replace("\n", " ")
    return body


def main():
    # 从匿名捕获中提取去重后的 GET API（排除遥测/日志类）
    cap = json.load(open(r"D:\scan\_figma_hunt\anon_capture2.json", encoding="utf-8"))
    skip = ("web_logger", "figment-proxy", "sentry", "rum", "datadog", "statsig", "metrics")
    targets = []
    for r in cap["reqs"]:
        method, url = r[0], r[1]
        if method != "GET" or "/api/" not in url or not url.startswith("https://www.figma.com"):
            continue
        if any(s in url for s in skip):
            continue
        if url not in targets:
            targets.append(url)

    anon = anon_session()
    auth = auth_session()

    print(f"对比 {len(targets)} 个 GET API（匿名 vs 登录态）\n")
    for url in targets:
        try:
            ra = anon.get(url, timeout=20)
            rb = auth.get(url, timeout=20)
            same = ra.status_code == rb.status_code and ra.text[:80] == rb.text[:80]
            mark = "SAME" if same else "DIFF"
            print(f"[{mark}] {url.split('/api/')[1][:90]}")
            print(f"   anon: {ra.status_code} len={len(ra.text)}  {summarize(ra.text)}")
            print(f"   auth: {rb.status_code} len={len(rb.text)}  {summarize(rb.text)}")
        except Exception as e:
            print(f"[ERR] {url[:90]} -> {e}")


if __name__ == "__main__":
    main()

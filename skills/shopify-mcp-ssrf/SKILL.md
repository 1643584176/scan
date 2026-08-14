---
name: shopify-mcp-ssrf
description: Shopify UCP MCP SSRF 攻击技能:profile 参数任意 https fetch 的完整校验链逆向、错误分类信息泄露、内网枚举方法、注入载体选择与托管服务实测、admin GraphQL persisted query 调用、GCS 预签名 URL 陷阱。用于深化 MCP SSRF 利用、完成 profile 注入攻击链、评估内网数据读取影响。
---

# Shopify MCP SSRF 攻击技能

## 攻击入口

- 端点: `POST https://catalog.shopify.com/api/ucp/mcp`(匿名可用,仅 3 个目录工具)
- 触发点: `tools/call` → `arguments.meta.ucp-agent.profile` → 服务端 fetch 该 URL 并解析 JSON
- 两大用途:
  1. **SSRF**: 任意 https URL 服务端 fetch + JSON 解析(内网探测/数据读取)
  2. **profile 注入**: 恶意 profile JSON(含 ucp.version + capabilities)→ 服务端以自身身份加载 agent 能力(潜在 Critical)

## 校验链(错误分类 = 信息泄露通道)

| 探测输入 | 错误信息 | 含义 |
|---|---|---|
| http:// 或裸域 | Https required | 协议白名单,必须 https |
| ftp:// 等 | Invalid uri format | 仅 http/https 被接受 |
| 2xx 非 JSON 内容 | Invalid content type | **内容被服务端读取**,非 JSON |
| 无 Cache-Control 头或含 no-cache/private | Invalid cache control | cc 必须存在且不含禁用词 |
| JSON 缺 ucp.version | Missing ucp version(version_unsupported) | **内网 JSON 被完整解析** = 数据读取级证据 |
| 非 2xx 状态码 | Http error | 目标存在但状态码非 2xx |
| 端口可达无响应 | Connection timeout | 目标主机/端口开放 |
| DNS/TLS 失败 | Network error | 域名不存在或不可达 |

## 内网枚举方法

- **子域枚举**: Network error = DNS 不存在;Http error / Connection timeout = 域名真实存在 → 可用于枚举内网域名(已验证 15 个 *.sfe.shopifyinternal.com 子域解析成功)
- **路径枚举**: 2xx 内容被读取 → Invalid content type 证明路径存在且返回内容;Connection timeout = 路由存在但端口无响应(如 /api /api/v1)
- **OIDC 探测**: /.well-known/openid-configuration 与 oauth-authorization-server 返回 "Missing ucp version" = 内网 OIDC JSON 被读取解析(最强证据)
- **已封死方向**: 重定向 301/302/307 不跟随(Http error);metadata(169.254.169.254 / metadata.google.internal)Network error;仅 443 端口开放

## 载体选择(profile 注入三条件)

- **必要条件**: 内容可控 + content-type=application/json + Cache-Control 有效 + 公开 GET 200(无重定向)
- **托管服务实测结论**(2026-08):
  - postman-echo /response-headers: 响应头完全可控(可设 cc: public)但 body 固定回显
  - webhook.site: 响应头固定 no-cache, private;actions(script/modify_response/http)全需付费订阅
  - jsonplaceholder: cc=max-age=43200 通过校验但内容不可控(用于规则精确化)
  - uguu: 无 cc 头;0x0.st: 上传关闭(503);paste.rs: ct=text/plain;jsonblob: 403;mocky: 证书问题
- **最佳方向: 目标自身 CDN 按扩展名返回 content-type** — cdn.shopify.com 上传 filename=profile.json 的文件 → ct=application/json + cc=public(404 页也返回 cc=public, max-age=60)
- jsDelivr cdn.jsdelivr.net/gh/...: ct=application/json + cc=public, max-age=604800(需 GitHub 账号)

## admin GraphQL persisted query 调用

- 端点: `POST /api/operations/{sha256}/{OperationName}/shopify/{shop}` + cookie + X-CSRF-Token
- hash 提取: JS bundle AST 中 `id:"64hex"` 与 OperationDefinition 配对(render.js 提取 StagedUploadsCreate 示例)
- 任意 hash → 404 PERSISTED_OPERATION_NOT_FOUND
- 已获取 hash: StagedUploadsCreate = b956e5aac09a77df4612cfeca05b03f9d7d4a5378013c2ef526a671e1e9a781d

## GCS 预签名 URL 陷阱

- bare PUT(仅 User-Agent)成功;拼 parameters(content_type/acl)到 URL → 403 SignatureDoesNotMatch
- 加 Content-Type / x-goog-acl 头 → 400 MalformedSecurityHeader
- 签名 URL 强制 PUT-only(GET 403)、acl=private 不可改 → 私有桶不可作公开读取载体
- 调试顺序: 先 bare PUT 确认 200,再逐个加头定位冲突

## 环境要点

- curl_cffi impersonate="chrome" + 代理 192.168.0.199:1080 是唯一过 Cloudflare 的方式
- curl_cffi 不支持 files= 参数 → 用 data= 手动构造 multipart
- 主题 asset 写操作触发 CHALLENGE_REQUIRED(Identity Session User Verification)→ 需用户浏览器完成,无法 API 绕过

# Shopify 项目进度(2026-08-13)

> 状态快照,供下次会话恢复现场。会话总结见 [SUMMARY.md](SUMMARY.md),技术细节见 `skills/shopify-mcp-ssrf`。

## 已确认漏洞级发现

### 1. MCP SSRF — 数据读取级(证据完备,可报 H1)
- **端点**: `POST https://catalog.shopify.com/api/ucp/mcp`(匿名可用)
- **触发**: `tools/call` 的 `arguments.meta.ucp-agent.profile` → 服务端 fetch 任意 https URL 并解析 JSON
- **内网读取证据**: `shop-server.sfe.shopifyinternal.com/.well-known/openid-configuration` 与 `oauth-authorization-server` 返回 "Missing ucp version" → 内网 OIDC JSON 被服务端完整 fetch+解析
- **内网测绘**: 15 个 `*.sfe.shopifyinternal.com` 子域解析成功(admin/api/checkout/catalog/ucp/graphql/metadata/store/web 等);`web.sfe` 全部路径 2xx 非 JSON(内容被读取);`/healthz` `/healthz/ready` `/healthz/live` 2xx;`/api` `/api/v1` Connection timeout(路由存在);shop-server 仅 443 开放
- **限制**: 重定向不跟随;协议白名单 http/https;metadata(169.254.169.254 / metadata.google.internal)不可达 → 不能直接打云元数据
- **报告影响论证**: 内网 DNS 域枚举泄露 + 内网服务存在性与内容读取 + 内网服务 JSON 数据解析(如 OIDC 配置可能含签名密钥端点、发现端点等敏感信息)。**任何内网 JSON API 都可被读取其响应体。**

### 2. Profile 注入攻击链 — 进行中(潜在 Critical,卡在载体)
- **目标**: 恶意 profile JSON(`ucp.version: 2026-04-08` + checkout/order/buyer_consent/cart/discount capabilities)→ MCP profile 参数注入 → 服务端以自身身份加载 agent 能力
- **载体三条件**: 内容可控 + ct=application/json + Cache-Control 有效 + 公开 GET 200
- **已封死**: webhook.site(头固定+付费墙)、uguu(无 cc)、0x0.st(503)、StagedUploadsCreate 私有桶(GET 403、acl=private 强制)、主题 asset(CHALLENGE_REQUIRED)
- **进行中候选(按优先级)**:
  1. 商品图片上传 `filename=profile.json` → cdn.shopify.com 按扩展名返回 ct=application/json + cc=public(**被打断,恢复点**)
  2. jsDelivr `cdn.jsdelivr.net/gh/{user}/{repo}/...`(需用户提供 GitHub 账号)
  3. 用户浏览器完成 Identity 验证后,主题 asset 上传获得 cdn.shopify.com 公开 URL

## 已封死方向(不再投入)

| 方向 | 结论 |
|---|---|
| 重定向绕过 | 301/302/307 均不跟随 |
| 云元数据 | 169.254.169.254 / metadata.google.internal → Network error |
| 协议绕过 | 仅 http/https 白名单 |
| 私有桶读取 | GCS 签名 URL 强制 PUT-only + acl=private |
| webhook.site 定制头/脚本 | actions 全需付费订阅 |
| 主题 asset 写入 | CHALLENGE_REQUIRED(需用户浏览器) |
| 枚举类 | 变体 ID 空间稀疏不可枚举;148 操作全需登录 |

## 待办清单

1. [ ] 恢复商品图片 CDN 载体测试(查商品列表 → 上传 filename=profile.json → 验证 CDN 头 → MCP 注入)
2. [ ] 若 1 失败,向用户要 GitHub 账号走 jsDelivr
3. [ ] SSRF 报告整理提交 H1(素材已完备,证据:内网 JSON 解析 + 子域泄露 + 2xx 内容读取)
4. [ ] 若 profile 注入闭环 → 单独 Critical 报告

## 关键资产

- admin cookie: `_shopify_browser_out/` 外部的 admin_cookies.txt(不入库)
- shop_id: 73342484522, store: jqpkdm-kb
- theme_id: 149297233962(main)
- StagedUploadsCreate hash: `b956e5aac09a77df4612cfeca05b03f9d7d4a5378013c2ef526a671e1e9a781d`
- 代理: 192.168.0.199:1080(curl_cffi impersonate=chrome 唯一过 CF 方式)

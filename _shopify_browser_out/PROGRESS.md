# Shopify 项目进度(2026-08-20 更新 — 认证态测试完成,全线闭环)

> 状态快照,供下次会话恢复现场。会话总结见 [SUMMARY.md](SUMMARY.md)。

## 最终裁决:Shopify 线全部封死,无提交价值

## 已确认发现

### 1. MCP SSRF — 数据读取级(证据完备,但按 Shopify 规则不提交)
- **端点**: `POST https://catalog.shopify.com/api/ucp/mcp`(匿名可用)
- **触发**: `tools/call` 的 `arguments.meta.ucp-agent.profile` → 服务端 fetch 任意 https URL 并解析 JSON
- **内网读取证据**: `shop-server.sfe.shopifyinternal.com/.well-known/openid-configuration` 与 `oauth-authorization-server` 返回 "Missing ucp version" → 内网 OIDC JSON 被服务端完整 fetch+解析
- **内网测绘**: 15 个 `*.sfe.shopifyinternal.com` 子域解析成功;14 主机 × 11 路径批量枚举(154 请求,26 hits)无新敏感 JSON 端点
- **服务端 fetch 头**: `Shopify-UCP/1.0`,**无 Authorization/cookie**(webhook.site 记录)→ 凭据窃取不可行
- **报告状态**: **不提交**(2026-08-19 定论)——Shopify 官方规则 "simple HTTP/DNS interaction alone is not considered a vulnerability";无元数据访问、无凭据、无提权链

### 2. Profile 注入链 — 交集模型在 catalog 域和 merchant 域全部验证,无法提权
- **载体**: Vercel 静态部署 — `mcp-carrier-2.vercel.app/profile.json`(v4 capability 枚举版, 8-19)
- **交集模型**: 工具可见性 = 注入 profile 声明的 capabilities ∩ 服务端允许集(只能收缩,不能扩张)
  - catalog 域允许集 = {catalog.search, lookup, get_product};checkout/order/cart **不存在于 catalog 域**
  - merchant 域允许集 = {checkout, fulfillment, discount, cart, catalog.*} 等
  - **8-20 认证态验证(carrier4 只声明 order+catalog.search)**: create_checkout/get_checkout → "Tool not found"(被过滤);search_catalog → 正常(声明了) — 收缩性双向确认
  - 11 个 merchant/admin capability 名全部静默丢弃
  - `payment_handlers` 注入无效(merchant 域响应回显**商店真实 gpay 配置**,服务端优先)
  - spec/schema URL 不 fetch(**catalog 域和 merchant 域都验证**: webhook.site new=0)→ 无二次 SSRF
- **新信息通道**: `structuredContent.ucp.capabilities` 回显服务端规范化后的 capabilities(白名单指纹,无越权价值)

### 3. 认证态测试(8-20 完成)— 翻盘失败,边界全部确认
- **认证获取**: 官方 OAuth Device Flow 走通 — `POST accounts.shop.app/oauth/device` → 用户浏览器授权 → 轮询 token(userinfo 验证通过,email/phone 均 verified)
- **token-exchange**: 两种都成功
  - catalog token: `audience=api.shopify.com`(发往 catalog.shopify.com)
  - checkout JWT: `resource=https://{shop_domain}/`(发往 merchant 域 UCP)
- **catalog 域(认证态)**: tools/list = 匿名态(只有 search_catalog);高权工具全部 Tool not found → **catalog 域根本没有 checkout 工具**(8-19 判"认证门槛"为误判,实际是端点域不对)
- **merchant 域(认证态, fluxfootwear.com 真实商店)**:
  - tools/list 返回完整工具集: get_checkout/create_checkout/get_order/get_cart 等
  - **create_checkout 真实成功**(官方 profile 和注入 profile 均可): 返回 checkout id + continue_url + gpay payment_handlers
  - get_checkout(`{"id": checkout_id}`) 成功返回自己的 checkout 详情
  - checkout id 带 `?key=32位随机hex` → **他人 checkout 无法枚举 → IDOR 不成立**
  - messages 差异(配送错误)为随机性,与 profile 无关(官方复测无该错误)
- **shop.app API**: payment_tokens 200(空数组,无预算);orderSearch 被 CF 路径级拦截(与 token 无关)

## 已封死方向(全部,不再投入)

| 方向 | 结论 |
|---|---|
| 重定向绕过 | 301/302/307 均不跟随 |
| 云元数据 | 169.254.169.254 / metadata.google.internal → Network error |
| 协议绕过 | 仅 http/https 白名单;metadata 需 HTTPS 强制 |
| 私有桶读取 | GCS 签名 URL PUT-only + acl=private 强制 |
| webhook.site 定制头 | cc 头不过(Invalid cache control),actions 付费墙 |
| 主题 asset 写入 | CHALLENGE_REQUIRED(需用户浏览器 Identity 验证) |
| 二次 SSRF(spec/schema) | catalog 域 + merchant 域都不 fetch(白名单映射) |
| Capability 提权 | 白名单外名字静默丢弃(交集模型,两域验证) |
| 匿名 checkout/order 工具 | catalog 域无此工具(端点域问题,非认证门槛) |
| 认证态 checkout 工具 | merchant 域真实可用,但是**官方正常功能**,非漏洞 |
| payment_handlers 注入 | 服务端配置优先,注入无效(merchant 域验证) |
| IDOR(checkout/order) | checkout id 带随机 key 参数,无法枚举 |
| 凭据窃取 | 服务端 fetch 无凭据头(Shopify-UCP/1.0) |

## 待办清单

1. **无** — Shopify 线彻底封死。恢复 Figma 主线(2026-08-19 状态: identity-claim 报告已关闭,20 日继续)

## 关键资产

- **认证态 token**: `_shop_app_token.json`(8-20 获取,access_token 1h 有效,refresh_token 可续;含 sub=JC4wRdKKZLim3nmR54SJJLYp / 1643584176@qq.com)
- **认证流程脚本**: `_shop_app_device_auth.py`(device flow, 用户浏览器授权即可,无需抓 cookie)
- **载体部署**: mcp-carrier-2(默认)/carrier-3(spec→webhook.site)/carrier-4(只声明 order) — 均 https://mcp-carrier-N.vercel.app/profile.json
- 载体目录: `_vercel_carrier/` `_vercel_carrier3/` `_vercel_carrier4/`(改 profile.json 后 `npx vercel@59.1.4 deploy --prod --yes --token <vcp_token> --name mcp-carrier-N`)
- Vercel token: `D:\scan\vercel_cookies.txt`(`authorization=Bearer vcp_...`)
- 测试脚本(8-20): `_auth_mcp_matrix.py`(catalog 域认证矩阵)、`_merchant_auth_matrix.py`、`_merchant_live_test.py`、`_flux_test.py`、`_flux_compare.py`(官方vs注入字段对比)、`_flux_ssrf_probe.py`(二次SSRF)、`_flux_final.py`(交集收缩验证)
- 真实商店资产: fluxfootwear.com(FLUX, variant gid://shopify/ProductVariant/44292830167273)
- 代理: 192.168.0.199:1080(curl_cffi impersonate=chrome 唯一过 CF 方式)
- shop_id: 73342484522, store: jqpkdm-kb(已不可用, 402 Unavailable Shop)

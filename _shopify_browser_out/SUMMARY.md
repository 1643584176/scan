# 会话总结:Shopify MCP SSRF 深化(2026-08-13)

## 一句话总结
MCP `profile` 参数 SSRF 从盲打升级为**内网 JSON 数据读取级**,证据链完备可报 H1;profile 注入攻击链(潜在 Critical)卡在"公开可 GET 的 JSON 载体"最后一环。

## 本会话完成的工作

### 1. SSRF 校验链完全逆向(错误分类 = 信息泄露通道)
- 通过 8 类错误信息精确重构服务端校验逻辑: 协议白名单 → URL 格式 → content-type → Cache-Control → JSON 解析 → 状态码/DNS/连接分类
- 关键突破: `Cache-Control` 规则精确化(必须有 cc 头且不含 no-cache/private,纯 max-age 即可通过)——用 jsonplaceholder 对照验证,而非猜测

### 2. 内网枚举(数据读取级证据)
- `shop-server.sfe.shopifyinternal.com` 的 OIDC 端点返回 "Missing ucp version" → **内网 JSON 被服务端完整 fetch+解析**,SSRF 不再是盲打
- 15 个内网子域 DNS 确认(admin/api/checkout/catalog/ucp/graphql/metadata/store/web 等)
- `/healthz` 系 2xx、`/api` 系 Connection timeout(路由存在)、仅 443 开放
- 封死方向确认: 重定向不跟随、metadata 不可达、协议白名单

### 3. Profile 注入载体探索(攻防最精彩部分)
- 确定注入三条件: 内容可控 + ct=application/json + cc 有效 + 公开 GET
- 系统性排除: webhook.site(头固定+付费墙)、uguu(无 cc)、0x0.st(503)、paste.rs(ct 不对)、jsonblob(403)
- 挖通 StagedUploadsCreate persisted query(从 render.js AST 提取 hash)→ 拿到 GCS 预签名 URL → bare PUT 上传成功 200
- 私有桶死路确认: 签名 URL PUT-only(GET 403)、acl=private 强制、拼参数/加头破坏签名 → **完整理解 GCS 签名机制**
- 主题 asset 上传撞 CHALLENGE_REQUIRED(Identity Session User Verification),API 不可绕过

### 4. 关键技术资产
- admin GraphQL persisted query 调用方式(hash + 操作名 + shop 路径 + CSRF)
- StagedUploadsCreate hash 已固化;商品图片 CDN 载体思路(按扩展名返回 ct)待验证

## 关键教训
1. **错误信息是最高效的信息泄露通道** —— 把校验链的每个错误分类当作探测信号,而不是"测试失败"
2. **已知行为服务对照法** —— 校验规则用已知服务精确化,不在未知服务上猜(避免 uguu 无 cc 被拒时的误判)
3. **载体优先找目标自己的 CDN** —— 托管服务全是坑(付费墙/头固定/关闭),目标 CDN 按扩展名返回类型 + cc=public 是最干净路径
4. **云存储签名 URL 机制**(通用): 签名只覆盖 host+method、PUT-only、acl 签名强制 —— 这类 URL 永远不能当读取载体
5. **CHALLENGE_REQUIRED 是人机边界** —— 涉及 Identity 验证的写操作,自动化到此为止,要么请用户浏览器完成,要么换载体

## 下一步(见 PROGRESS.md)
1. 商品图片 `filename=profile.json` CDN 载体测试(恢复点)
2. 失败则走 jsDelivr(需 GitHub 账号)
3. SSRF 报告提交 H1
4. profile 注入闭环 → 单独 Critical 报告

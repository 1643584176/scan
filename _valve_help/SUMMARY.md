# help.steampowered.com 安全评估总结

**日期**: 2026-08-03
**目标**: https://help.steampowered.com (Steam Support,Valve HackerOne 范围)
**状态**: 未发现可利用漏洞(未登录面)

---

## 1. 指纹与技术栈

| 项目 | 结果 |
|---|---|
| Web 服务器 | nginx(经 Akamai CDN,china_eccdnx 加速) |
| 框架 | 服务端渲染 + jQuery 1.8.3 + help.js wizard SPA 流程 |
| 会话 | sessionid(Secure + SameSite=None)+ steamCountry cookie |
| 安全头 | X-Frame-Options: DENY; CSP 完整(script-src 含 recaptcha/hcaptcha,frame-src 含 login/steamcommunity/store/partner/dota2); HSTS preload |
| 登录体系 | login.steampowered.com 统一登录(data-props login featuretarget + CLoginPromptManager) |

## 2. 已测攻击面与结论

### 2.1 参数反射 / XSS —— 全部排除
- `wizard/HelpWithGame/?appid=` :非数字被丢弃;纯数字仅反射进 hreflang 链接(URL 编码)
- `wizard/HelpWithGame/SearchGame/?query=` :特殊字符 URL 编码,无实体化风险面
- `wizard/ScamUserSearch/?text=` :三层防护(URL 编码 + JSON `\/` 转义 + HTML 实体),data-props redirectUrl 不可断
- `faqs/view/:id` :任意 ID 格式均 200(无效 ID 回 FAQS 列表页);特殊字符仅 URL 编码进 hreflang
- `wizard/HelpWithLoginInfoReset/?account=` :payload 零反射
- `wizard/Login?redir=` :见 2.2
- `AjaxSearchResults` 的 `search_text` 字段:JSON 原样转义返回,JS 侧仅 `$('#help_search_support_input').val(search_text)` 回填,无 DOM 注入

### 2.2 Open Redirect —— 排除
- `wizard/Login?redir=`:
  - 绝对外域 URL(`https://evil.com/...`)→ **403 拦截**
  - 协议相对 `//evil.com` → 服务端强制拼接 `https://help.steampowered.com/en/` + redir → 结果仍在站内
  - JSON 转义完整(`"` → `\"`),无法注入 data-props 的 redirectUrl
  - 反斜杠 `\evil.com` → JSON 中 `\\`,浏览器规范化为站内路径
- `AjaxAccountRecoveryGetNextStep` 响应的 `redirect` 字段(`window.location = data.redirect` 消费):
  - `account`/`issueid` 参数可反射进 redirect URL
  - **但仅保留前导数字**:`999/1`→`999`、`9-9`→`9`、payload 全丢弃 → 无法逃逸 host

### 2.3 未登录 API 端点枚举(36 个 wizard AJAX 端点)
- **关键认知**:所有端点需 POST body 内 `sessionid` 参数(非 cookie)才放行,否则 `{"success":15}`
- 未登录可用且有响应的:
  - `AjaxSearchResults/` → 200,返回游戏搜索结果 HTML(无用户输入反射)
  - `AjaxSendAccountRecoveryCode` → `{"success":true}`(无 hash 时疑似假成功;为防触发真实短信,未重复调用)
  - `AjaxCheckPasswordAvailable/` → 密码强度检查,非存在性检测
  - `AjaxAccountRecoveryGetNextStep` → redirect 字段(见 2.2)
  - `getrsakey/` → RSA 公钥,用户名随机/存在响应一致 → 无用户枚举
  - `setlanguage/` → 需 sessionid,语言偏好修改(低危)
- 其余(退款/工单/RMA/账户恢复变更类)均返回错误或空 → 需登录态

### 2.4 其他
- `getmenuactions/`、`rendercaptcha/`、`RefreshCaptcha` 均为标准功能
- 登录引导页(ScamUserSearch 未登录返回的 HTML)redirectUrl 构造与 2.2 相同防护

## 3. 结论

未登录攻击面防御到位:输入过滤 + URL 编码 + JSON 转义 + 服务端前缀拼接 + 数字白名单,无 XSS / open redirect / 信息泄漏。带登录态的 wizard 流程(退款、账户恢复)需要真实账号,超出当前能力。

**建议**: 转测其他可达目标(partner.steampowered.com / steam.tv / api.steampowered.com 公开端点)。

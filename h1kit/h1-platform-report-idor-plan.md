# H1 平台 — 越权读他人私有漏洞报告(只读)攻击面规划

> 目标:hackerone.com/security(HackerOne 平台自身 bounty)
> 漏洞假设:报告对象(report_id 为递增整数)的读取授权存在缺口——非 reporter/非 program member 可读私有报告内容
> 纪律:只读、零破坏;双账号或程序成员基线互测;不碰 H1 staff/其他平台用户敏感数据

## 报告对象可见性模型(基线)
- report id:递增整数(hackerone.com/reports/{id})
- 正常可见:reporter、program team members(admin/team)、H1 staff、被@的协作者;公开披露后任何人可读
- 私有报告:reporter + program members + H1 staff

## 候选读取面(按优先级)

### 1. GraphQL(前端主数据通道,IDOR 高发区)
- 端点猜测:hackerone.com/graphql、/api/graphql、/graphql?(浏览器 network 确认)
- 测试:query 拉取 report(id)/activities/attachments/comment;改 id 为他人私有报告
- 变体:aliases/batch/内嵌 fragment、__typename 混淆、深层字段(applied_to_program 的私有元数据)

### 2. 登录态 HTML 内嵌数据(SSR/预载)
- GET /reports/{id} 登录态返回 HTML —— 检查是否有预载 JSON(report 内容/时间线)
- 若 SSR 按 URL 渲染而鉴权只在 API 层 → 直接改 id 读(最朴素的洞)

### 3. 旧 JSON 端点家族(已知历史洞 #2487889: POST /bugs.json)
- 变体:/bugs.json 参数变体、/reports/{id}.json、/api/bugs、/internal 类路径
- 已知洞是 2024 披露已修——找同族变体

### 4. 附件/资源 CDN
- 报告附件、截图 URL(CDN 域名)——若签名 URL 可枚举/无绑定 → 直接读附件内容

### 5. 导出/分享面
- 报告 PDF/导出、share link(token 枚举/绑定缺失)、timezone/ics 日历订阅(报告时间线?)

### 6. 搜索/通知面
- 全局搜索 API 是否索引私有报告内容(搜索结果泄露)
- 通知 API(bell)按 report_id 拉取时鉴权

### 7. 程序上下文注入
- 作为某程序 bounty hunter,请求带 program 上下文的 report 读取 → 换 program 参数读其他程序的私有报告

## 测试方法(基线优先)
1. 基线 A:自己的报告(若有)读 OK;无登录态读私有报告 → 拒绝
2. 基线 B:自己受邀程序内,他人提交的私有报告(同程序 hunter 视角)——**真实越权面核心**
3. 注入:对每个候选面改 report_id/参数,对比 200 vs 403/404/空
4. 全程只读;发现的私有内容不扩散(截图最小化)

## 待用户提供
- [ ] hackerone.com/security 规则全文(scope 域名列表、测试边界、禁止项)
- [ ] 登录态请求样本(浏览器 network 复制任一 hackerone.com 请求 curl,含 cookie)
- [ ] 账号拓扑:几个 H1 账号?受邀程序成员身份?(决定互测基线方案)

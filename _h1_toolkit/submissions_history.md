# 已提交漏洞 → H1 回复结果档案

> 用途：提交新报告前参考**同类型漏洞的 H1 回复模式**，预判关闭/确认逻辑，优化报告措辞与利用链证据。
> 维护规则：每次收到 H1 回复（triage/关闭/奖励）由用户转发后，即时补充到本表并保留回复全文。

## 档案总表

| # | 日期 | 目标 | 漏洞 | 提交严重度 | 结果 | H1 核心回复逻辑 | 经验教训 |
|---|---|---|---|---|---|---|---|
| 1 | 2026-08-06 | Figma | livegraph PlanByFileKey 匿名泄露 billing Plan（stripeCustomerId/VAT） | HIGH / CWE-639 | **Informative 关闭** | Plan 绑定文件级读权限 = 预期行为；billing 标识符单独无法做金融交易/未授权访问；程序重点在"未授权访问用户数据" | ① 文件级权限传导的组织元数据不算越权——必须证明**用户数据的未授权访问**；② 留下口子："leverage into practical exploitation scenario 可重新评估"——需要把泄露数据下游消费成实际危害 |

## 详细记录

---

### #1 Figma PlanByFileKey → Informative（2026-08-17 关闭）

**提交内容摘要**：匿名 livegraph WebSocket 订阅 `PlanByFileKey` 视图，任何可读文件 key 返回所属团队/组织完整 Plan——stripeCustomerId、vatGstId（真实欧盟 VAT）、taxIdVerificationStatus、planRecordId、升级审批设置、内部 feature toggles。11 个公开文件验证；付费 pro 团队 Themesberg/Flowbite 实测（cus_J1xwCSokJo6SMU / RO42244256）。PlanByOrgId/PlanByTeamId 匿名被拒、PlanByFileKey 放行——授权模型不一致证明 bug。

**H1 回复全文**（h1_analyst_akaay，8 小时后关闭）：

> Thanks for your report, @boboli
> After further investigation, there do not appear to be any security impact as a result of the behavior you have mentioned.
> The Plan object being returned through PlanByFileKey subscription is actually tied to file-level read permissions, which seems to be working as intended by the system. When a file is made public by the owner, certain organizational metadata like plan tier, billing status and feature configurations are exposed along with it. While billing identifiers such as stripeCustomerId and VAT numbers are included in the response, these alone cannot be used to perform any financial transactions or gain unauthorized access to the account. The program is primarily focused on unauthorized access to user data, and in this case the file sharing permissions are behaving as expected where public files reveal some organizational context to anyone who can view them.
> As a result, we will be closing this report as informative. If you are able to leverage this into a practical exploitation scenario, we will be happy to reevaluate this report. This will not have any impact on your Signal or Reputation score.

**关键解读**：
1. **判定标准**：公开文件暴露组织上下文 = 文件共享的预期行为；授权模型矛盾（多入口不一致）不足以推翻"intended"
2. **数据敏感性判级**：stripeCustomerId/VAT 被视为"billing identifiers"，无直接交易能力 → 不构成安全影响
3. **程序重心**："unauthorized access to user data"——用户数据（文件内容/个人信息）才是 scope 核心
4. **翻盘路径**（H1 明确给出）：把泄露数据杠杆化成实际利用场景——例如利用 stripeCustomerId 完成对账户的未授权操作、访问未公开用户数据

---

### 待补充记录位

- **Shopify MCP profile SSRF**（2026-08 中）：数据读取级证据链完备（内网 OIDC JSON 被解析），提交后待记录回复
- **Figma foundry downloadUrl SSRF**（2026-08-12 草稿）：公网 fetch 成立、内网隔离——提交后待记录
- **Wolt checkout 价格操纵 CWE-602**：已提交，待记录回复

## 提交前自查清单（基于 #1 教训）

1. ☐ 泄露的是**用户数据**（文件内容、个人信息、私有消息），还是组织元数据？后者易被判 Informative
2. ☐ 数据标识符（ID/号）能否**下游消费**成实际动作？（改密码、访问账户、发起交易）
3. ☐ 是否存在**授权模型矛盾**证据（同数据多入口权限不一致）？有则写，但不足以单独定性
4. ☐ 是否明确写出"能做什么"（利用链），而非只写"泄露了什么"（数据面）？
5. ☐ 针对"intended behavior"防御：是否预判并反驳"公开文件暴露上下文是预期"这一论调？

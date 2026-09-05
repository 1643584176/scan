# Eternal (Zomato 系) H1 规则与测试基线 — 完整版

> 更新: 2026-09-05(用户提供 H1 policy 全文)。程序: https://hackerone.com/eternal

## 进行中: SQLi Campaign (2026-09-05 ~ 2026-09-13 UTC)
- 每份 valid SQLi 报告: Critical/High 1.5x; Medium/Low 1x(标准价)
- **First Blood: 首个 valid Critical SQLi +$500 / High SQLi +$250(各一次)**
- Campaign 价表(乘数后): Critical $3,000-$6,000 / High $1,500-$3,000 / Medium $300-$1,000 / Low $100-$300
- 报告须 9/5-9/13 UTC 内提交且为 new; 标准规则/scope/CVSS 适用
- SQLi 定级(程序标准): Critical = 读 PII/敏感数据 或 数据库全读写;
  High = 有限权限用户执行查询(limited access user)
- 注意 Tier 表价(下表)与 campaign 表可能叠加口径: campaign 表自述 "1.5x multiplier applied per asset table"

## 赏金表(标准, 按 Tier + CVSS)
| Tier | Low | Medium | High | Critical |
|---|---|---|---|---|
| Tier 1 | $100-300 | $300-1,000 | $1,000-2,000 | $2,000-4,000 |
| Tier 2 | $100-200 | $200-500 | $500-1,000 | $1,000-2,000 |
| Tier 3 | $50-100 | $100-250 | $250-500 | $500-1,000 |
- 例: CVSS 10.0 Crit = $4,000(Tier1); CVSS 9.5 = $3,000; 实付按最终 CVSS
- 90 天实付均值: Low $100 / Med $206 / High $713 / Crit $900

## Asset Tiers(2025-11-19 版, 完整)
**Tier 1**(核心):
- *.zomato.com / *.zomans.com / *.runnr.in / blinkit.com
- iOS: 434613896 (Zomato) / 960335206 (Blinkit Customer) / 6670203019 (Blinkit Bistro)
- Android: com.application.zomato / com.grofers.customerapp / com.blinkit.bistro / com.zomato.delivery
- **https://mcp-server.zomato.com/mcp (Zomato MCP Server)**
**Tier 2**:
- *.blinkit.com / *.hyperpure.com / *.grofer.io / *.grofers.com / www.district.in
- api.grofers.com / api2.grofers.com
- Android: com.application.zomato.district / iOS: 6670536058 (District)
**Tier 3**:
- *.district.in / *.insider.in / *.edition.in / *.ticketnew.com / *.eternal.com

## Scope 页 49 资产表(2026-03-24 更新, H1 scope 页)——独立于 Tier 分组的资产维度
**Eligible(Critical max)**:
- 域: winecellar.zomato.com(0 报, 2017 加入)/ blinkit.com(20)/ bistro-api.blinkit.com(1)/ api.grofers.com(4)/ api2.grofers.com(8)
- Wildcard: *.zomato.com(545, 43%)/ *.runnr.in(40, 2026-03-24 scope 更新)/ *.hyperpure.com(42)/ *.insider.in(29)/
  *.ticketnew.com(27)/ *.district.in(25)/ *.zomans.com(20, AWS 内网应用, 兴趣=unrestricted access/internal data)/
  *.tktnew.com(8)/ *.eternal.com(1)/ *.edition.in(5)/ *.zdev.net(5)/ *.grofer.io(1)/ http://*.grofers.com(8)
- URL: mcp-server.zomato.com/mcp(3, 2025-09-23 加入)/ Data Protection Program(9)
- Apps: com.application.zomato(63)/ 434613896 iOS(10)/ com.grofers.customerapp(2)/ 960335206 iOS(2)/
  com.blinkit.bistro(2)/ 6670203019 iOS(0)/ 6670536058 iOS(0)/ com.application.zomato.district(6)
- 分组: Tier 1(11)/ Tier 2(5)/ Tier 3(7)/ All Assets (other than Blinkit)(14)
**Ineligible(明示)**:
- www.zomatobook.com / success.zomato.com / send.zomato.com / community.zomato.com /
  blog.zomato.com / business-blog.zomato.com / dev.hyperpure.com / devapi.hyperpure.com /
  devpod.hyperpure.com / staging*.runnr.in / *.blinkit.support / *.zomatoportugal.com /
  *.bstro.io / *.ali.zomans.com / com.application.zomato.ordering /
  com.application.zomatomerchant(商家 app, 2018)/ Scope Questions(Feb 2020)

## 关键新发现
- **bugbounty.runnr.in**: staging*.runnr.in OOS, 但规则明示存在专用 replica 测试环境
  bugbounty.runnr.in —— 官方授权的测试面(团队自建, 可能保留漏洞+弱防护)
- winecellar.zomato.com: 2017 加入至今 **0 resolved** —— 冷门 Tier1 域, 竞品少
- mcp-server 2025-09 才加入, 仅 3 报 —— 新 AI 资产仍在早期
- *.zomans.com 规则自述兴趣: unrestricted access / internal data —— 内网面优先
- com.application.zomatomerchant = Ineligible(与 tier 页 submit-only 不符, 以 scope 页为准不碰)

## 报告规则
- 提交时必须选正确资产(选错延迟/重派)
- 只用测试账号; 禁 DoS/垃圾流量/高音量自动化
- **测试时请求带 header: X-Hackerone: <h1_username>**
- 仅首位报告者得赏金; 公开披露先于修复 = 取消资格
- 多报告同一模式弱点 = 仅首个确立模式的得全赏金
- CVSS 由 Eternal 团队终定, 赏金最终裁量权在团队

## Out-of-scope / 不付(精选)
- Core Ineligible Findings(H1 平台标准); 商户/合作方端点; dev/staging 实例
- blog/business-blog/community/send/success.zomato.com; *.zomatoportugal.com; *.bstro.io
- www.zomatobook.com; edition.in 裸域; *.ali.zomans.com; staging*.runnr.in
- Zomato Legends 相关一律 informational 不付
- 凭证泄露: 2FA 在场 = informational; 泄露凭证报告 $50-150/份(雇员个人/客户/商户账号不在范围)
- Broken Link Hijacking = low 不付; SSL pinning/root detection bypass 不付
- 公开 PII 可检索、用户名/邮箱枚举不付
- 促销滥用/推荐码滥用/现金返还逻辑(OOS 已知)
- CSRF on www.zomato.com/php/ 和 /clients/ 不付
- Rate limiting/暴力破解、Cache Poisoning DoS、Open redirect(无附加影响)、Self XSS、Tabnabbing、
  CSV injection(无 PoC)、Clickjacking(无敏感操作)、TLS/CSP/HttpOnly/Secure 最佳实践缺失、
  banner/版本披露、MITM 前提攻击 —— 全不付
- 未知资产先 Scope Questions 询问

## Data Protection Program(并行专项)
- 被动数据暴露监测(不活跃测试): 公开 S3/API 泄露客户数据、GitHub/paste 泄露凭证验证
- 允许: 只读验证 Eternal 数据可达性; 禁: 活跃利用/爆破/横向/改删/大流量/社工
- 赏金 $100-500

## 严重性分级参考(程序示例)
- Critical: RCE / SQLi(读 PII 或 DB 全读写) / SSRF(非盲, 可 pivot 或拿凭证) / 批量 PII 泄露
- High: Stored XSS(非 HttpOnly cookie) / 凭证泄露 / 子域接管(有 PoC) / CSRF→ATO /
  ATO(无/少交互) / IDOR(敏感数据读写) / **SQLi(有限权限用户查询)**
- Medium: CSRF(改重要信息) / ATO(需交互) / IDOR(写) / Reflected/DOM XSS(cookie)
- Low: 目录列表 / XSS(无 cookie) / POST XSS(带 CSRF bypass) / 无 HTTPS 动态页 / 服务器信息页 / 未用子域接管

## 方法论映射(结合当前打法)
1. **SQLi campaign 窗口 8 天** —— 主攻方向, First Blood 可能已被抢(全球 hunter), 但 1.5x 持续
2. SQLi 高发面推断:
   - 遗留收购品牌(Tier3: ticketnew/tktnew/insider/edition/district.in + Tier1 runnr.in/zomans.com)
     —— 老代码未重构, SQLi 概率最高
   - Zomato API 查询类参数(搜索/筛选/排序/分页/城市 ID)
   - 移动 app API(需抓包/逆向)
   - mcp-server(Tier1, 新 AI 资产——MCP 工具参数 SQLi? 少见但新)
3. 历史公开洞型: CL.TE request smuggling 偷 X-Access-Token(771666)、会话窃取、XSS、IDOR
   —— X-Access-Token 体系 + 老 PHP 端点(/php/ /clients/ 有 CSRF 豁免=可能遗留)
4. 测试约束: 低音量(禁大流量工具)、X-Hackerone header、测试账号

## 待办/依赖
- [ ] H1 username(写 X-Hackerone header 用)
- [ ] Zomato 测试账号(印度手机号注册)
- [ ] 子域/端点侦察(只读)后定注入候选

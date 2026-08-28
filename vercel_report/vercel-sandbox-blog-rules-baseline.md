# Vercel Sandbox $1M Challenge — 官方博客规则基线

> 来源: https://vercel.com/blog/one-million-dollar-hacker-challenge-for-vercel-sandbox
> 发布: 2026-08-18 | 作者: Andy Riancho (Vercel CTO)
> 用途: scope 权威概要离线基线(完整 known-duplicate 清单仅在 HackerOne 页面,需登录)

## 挑战参数

- **窗口**: 2026-08-18(周二) ~ 2026-09-01(周二),池耗尽则提前结束
- **池**: 最高 $1,000,000 USD
- **单报告上限**: $50,000 USD(跨租户读/改数据)
- 赏金按报告支付,scope 到单一 root cause,由 Vercel triage 按**最大可证明影响**定级

## 安全模型(博客原文要点)

- Vercel Sandbox 运行在裸金属 EC2 host 上;每个沙箱是独立的 Firecracker microVM(专用 guest kernel),microVM 内跑 Linux 容器承载用户代码
- **"The microVM, not the container, is the security boundary"** —— 安全边界是 microVM,不是容器
- 假设容器内代码完全敌对:容器内 root、microVM 内全内核访问、且有动机到达 host 或他人租户
- 网络侧边界在 **host 上(microVM 之外)**执行,沙箱内代码无法修改/禁用;sandbox firewall 拦截出站 TCP/DNS,按 operator 的 domain/CIDR policy 检查,可在边界注入凭据(凭据不进入 microVM)

## What we're looking for(合格范围)

**Compute boundary:**
- 逃逸 Firecracker microVM 到达 EC2 host
- 通过 compute 层到达另一租户沙箱(读/改/执行其中代码)
- 从一沙箱崩溃另一租户沙箱

**Network boundary:**
- 不跨 microVM 而击败 sandbox firewall:到达 operator 未授权的目的地
- 外泄数据
- 检索 brokered credentials

## Out of scope(官方原文)

> "Container namespace escapes that only reach the Firecracker guest OS are not in scope. Namespaces are a developer-experience feature, not the security boundary."

容器 namespace 逃逸仅到达 Firecracker guest OS → **不在范围**;namespace 是开发者体验功能,不是安全边界。

## Bounty 表

| Severity | Bounty |
|---|---|
| Critical | $25,000 – $50,000 |
| High | $10,000 – $25,000 |
| Medium | $5,000 – $10,000 |
| Low | $1,000 – $5,000 |

(完整 bounty 表+各 tier 示例漏洞类别在 HackerOne 页面)

## 提交要求

- 复现必须 live PoC(用 @vercel/sandbox SDK boot 沙箱,演示实际影响)
- 默认沙箱 OS 足够多数报告;只有 PoC 需要额外工具才用自定义镜像(Vercel Container Registry)
- **静态分析-only 不奖励**("We will not reward static-analysis-only findings; to issue a payout, we need to see the boundary break")
- 完整 bounty 表 + 各 tier 示例漏洞类别 → "The full bounty table, with example vulnerability classes for each tier, is on the HackerOne program page"

## Results and payouts(博客原文要点)

- **Triage 周期**: "We will triage reports from the day the program opens through one month after it closes" —— 从开赛日(8/18)起至闭赛后一个月
- 确认后支付赏金,并 credit 每位报告成立的研究者("we will pay bounties, ship fixes, and credit every researcher whose report holds up")
- **赛后公开复盘**: "After the program closes, we will publish a follow-up writeup of the techniques and the fixes we shipped" —— 结束后发布技术+修复总结(可留意后续博客,了解官方修复方向/新边界)

## 与 HackerOne 页面的关系

博客原文: "The full bounty table, detailed scope, and the list of known-duplicate classes are on the HackerOne program page."
→ 完整 known-duplicate(已知重复)清单**只在** hackerone.com/vercel_sandbox(SPA,匿名不可抓,需登录查看)

## 与官方报告回复判定的一致性

- 博客 "只到 guest OS 的 namespace 逃逸不算" ↔ #3955363/#3965216/#3972961 回复 "stays inside your own microVM → N/A"
- 博客 "compute boundary = EC2 host 逃逸/跨租户" ↔ 官方回复 "material new impact = EC2 host 新逃逸路径/跨租户/先前未知 host 写原语"
- 官方回复是对博客 scope 的逐案执行;提交前对照本基线 + 4 份 N/A 报告回复 + H1 页面 known-duplicate 清单三重自查

---
name: rule-baseline-first
description: Collect official program rules, full policy, Known findings list, and historical N/A report replies before investing in any bug bounty target or new attack direction; archive them and evaluate against the criteria before deciding to invest. Use when starting a new HackerOne program, proposing a new attack direction, or before drafting a vulnerability report.
---

# Rule Baseline First(规则基线先行)

**任何项目、任何新攻击方向,先收集并对照官方判定材料,再决定投入。没有完成基线对照,不投入测试、不写报告。**

## 为什么(教训来源)

Vercel Sandbox 4 份报告全 N/A、0 赏金(2026-08):"新根因≠新影响"——官方只认影响(host 逃逸/跨租户/新 host 写原语),不认根因新旧。火力全在官方明确排除的面上,是执行勤奋掩盖判断懒惰。避免方式:投入前先建判定基线。

## 核心原则:怀疑一切(任何时候,无条件)

任何情况下保持怀疑态度,两条铁律:

1. **"有问题" ≠ 漏洞不成立**:测试失败、有防御、有限制、负面证据,都只说明"这条路径没走通",不代表漏洞不存在。失败先怀疑方法、路径、环境,再怀疑漏洞本身。
2. **"没问题" ≠ 没有漏洞**:测试通过、看起来正常、官方排除清单覆盖、历史 N/A 判定,都不代表没有漏洞。没测出 ≠ 不存在;官方排除的是"已知原语",新根因、新影响、新路径、新延伸仍可能成立,继续怀疑。

基线材料(规则/政策/Known findings/N/A 回复)是**判定参考,不是思维枷锁**——用于排除已知,不用于终结思考。

## 触发场景

- 用户提出新项目/新目标,要求开始测试
- 提出新的攻击方向或攻击面(即使在同一项目内)
- 准备撰写或提交漏洞报告前
- 评估已有发现是否值得继续深挖

## 执行流程

### Step 1 收集官方规则

- **直接请用户提供**(用户明确偏好:规则/政策/Known findings/报告回复等登录后可见内容由用户直接复制提供)
- 官方公告/博客(challenge 公告通常含 scope 概要、bounty 表、out-of-scope 定义)——这个是公开页面,可尝试抓取
- **不要尝试自动抓取 HackerOne 项目页面**:纯 SPA,匿名返回空壳,HTML 无内嵌数据,WebFetch/Playwright/API 均不可行,已多次验证

### Step 2 收集完整政策

- In Scope / Out of scope(逐条)
- Bounty 表 + severity 判定规则(虚报罚则、最大可证明影响原则)
- Submission requirements(必含要素:PoC zip、各类 ID、漏洞类别、severity rationale)
- Disclosure policy / embargo 期限
- Rules of engagement(测试限制:qps、账号、stop-at-confirmation)

### Step 3 收集 Known findings 清单

- 完整清单只在项目页面(需登录);官方回复中点名的条目也要收集
- 注意:官方还有内部 tracker 查重——清单上没有 ≠ 可以提

### Step 4 收集历史 N/A 报告及官方回复

- 本项目已提交报告的官方回复(判定理由、点名的 Known findings 条目)
- 报告者自己的 self-close 理由(负面证据:如 COW 快照、NOT SHARED、CLOSED)
- 官方回复中出现的"合格标准"表述(如 "materially new impact" 的定义)

### Step 5 归档(遵循 vercel_report 模式)

目录结构(以 Vercel 为模板,见 `D:\scan\vercel_report\`):

```
<项目>_report/
├── <project>-blog-rules-baseline.md   # 官方博客/公告 scope 概要
├── <project>-h1-policy-full.md        # 完整政策全文(Known findings 高亮)
└── H1-<报告id>-<简短名>.md            # 每份历史报告:报告原文 + 官方回复 + 判定要点
```

- 每份归档含"判定要点(供复盘)"小节,提炼官方判定逻辑
- 判定标准同步记入长期记忆(project_introduction 类)

### Step 6 对照判定,列"不算漏洞清单"

提交/投入前逐项自查:

- [ ] 影响是否命中官方定义的合格影响(已演示的实际影响,不是升级路径/潜在影响)
- [ ] 对照 Known findings 逐条查重(含内部 tracker 风险)
- [ ] 是否与已提交报告重复/延伸(同攻击面延伸 = 高风险)
- [ ] 资产条目是否在范围内(以资产清单为准,非规则正文描述)
- [ ] PoC 是否 live 可复现(静态分析不算)
- [ ] 负面证据(自证局限:CLOSED/NOT SHARED/COW)是否会被官方引用为 N/A 理由——有则不写报告
- [ ] 报告必含要素是否齐备(PoC zip、ID、类别、severity rationale)

### Step 7 决策

- **不满足任何一项 → 不投入/不提交**:实验成果存档(标注"评估为 N/A 未提交"),转向其他方向
- **满足全部 → 再开始测试投入或提交**
- 官方明确邀请的方向(如"链成 host 逃逸/跨租户的跟进报告合格")优先
- **决策后仍保持怀疑**:
  - 排除清单只排除"已知原语和已演示影响",不排除新路径——被排除方向出现新根因/新影响时重新评估
  - 负面测试结果(防御生效、测试失败)先怀疑方法和路径,不急于对"该处无漏洞"下结论
  - 基线对照通过 ≠ 漏洞成立;只是获得投入资格,验证过程中继续怀疑

## 检查清单(每次基线建立后)

- [ ] 官方规则已收集(项目页/博客,注明来源与日期)
- [ ] In/Out of scope 逐条确认
- [ ] Known findings 清单已拿到(或明确缺口并已请用户提供)
- [ ] 历史 N/A 报告回复已归档
- [ ] "不算漏洞清单"已列出并与用户确认
- [ ] 判定标准已记入记忆

## 参考案例

Vercel 完整基线归档(活模板):`D:\scan\vercel_report\`
- [vercel-sandbox-blog-rules-baseline.md](D:\scan\vercel_report\vercel-sandbox-blog-rules-baseline.md)
- [vercel-sandbox-h1-policy-full.md](D:\scan\vercel_report\vercel-sandbox-h1-policy-full.md)
- H1-3955363 / H1-3954985 / H1-3965216 / H1-3972961(报告+官方回复归档)

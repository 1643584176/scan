# H1 (HackerOne) 平台工具包

> 用途：HackerOne 平台数据获取的**确定性调用知识** + 抓取工具 + 已提交漏洞回复档案。
> 原则：所有调用方式均已实测验证，以后直接使用本包，**禁止重新探测**。

## 目录结构

```
_h1_toolkit/
├── README.md              # 本文件：包导航
├── API.md                 # H1 GraphQL API 确定性调用知识（端点/查询/字段/限制）
├── submissions_history.md # 已提交漏洞 → H1 回复结果档案（提交前参考）
├── ANALYSIS.md            # 1000 条 hacktivity 报告思路分析（漏洞类型/高赏金样本/可复用模式）
├── scripts/
│   └── hacktivity_fetch.py  # hacktivity 列表抓取（disclosed/undisclosed 各 10 页）
└── data/
    ├── hacktivity_disclosed.json    # disclosed:true 数据（500 条）
    └── hacktivity_undisclosed.json  # disclosed:false 数据（500 条）
```

## 常用入口

- **查 API 怎么调** → `API.md`（不用重新探测）
- **看真实报告思路** → `ANALYSIS.md`（1000 条报告的模式提炼）
- **提交前参考回复模式** → `submissions_history.md`（已提交漏洞 → H1 回复）

## 快速调用

```bash
# 抓取 hacktivity（disclosed:true + disclosed:false 各 10 页，写入 data/）
python scripts/hacktivity_fetch.py
```

## 已提交漏洞回复档案（速查）

| 日期 | 目标 | 漏洞 | 提交状态 | H1 回复 | 关键措辞 |
|---|---|---|---|---|---|
| 2026-08-06 | Figma | livegraph PlanByFileKey 匿名泄露 billing Plan | HIGH/CWE-639 | **Informative 关闭** | "Plan 绑定文件级读权限是预期行为；billing 标识符单独不能做金融交易"；留下口子："leveraging into a practical exploitation scenario 可重新评估" |
| 2026-08-12 | Figma | foundry sync downloadUrl SSRF | 草稿待提交 | — | — |
| 2026-08 中 | Shopify | UCP MCP profile 参数 SSRF | 待提交 | — | — |
| 2026-08 | Wolt | checkout 价格操纵 CWE-602 | 已提交 | — | — |

详细回复全文见 `submissions_history.md`。

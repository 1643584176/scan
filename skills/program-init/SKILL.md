---
name: program-init
description: Initialize a HackerOne bug bounty target before any testing by fetching its program policy and scope. Use when the user names a new target site, switches the testing URL/domain, or asks to start testing a new program, so that every subsequent test stays inside the program rules and in-scope domains only.
---

# Program Init

每次切换测试目标(新网站 / 新 URL / 新项目)时,必须先完成目标初始化,再开始任何测试。**没有初始化的目标不开始测试。**

## 触发场景

- 用户给出一个新网站/项目名,要求开始测试
- 用户说"换目标"、"测这个网站"、"切换 URL"
- 需要确认某域名是否在测试范围内时

## 执行流程

1. **确认目标 handle**:用户给出网站名或 URL,确定对应的 HackerOne 项目 handle(如 `wolt` → `hackerone.com/wolt`)。不确定时先向用户确认项目名。
2. **运行初始化脚本**(在 `D:\scan` 下,用户名固定 `pccp`,不用传):

   ```bash
   python program_init.py <handle>
   ```

   脚本会用 Playwright 打开 HackerOne 规则页 + Scope and Rewards 页,输出到 `programs/<handle>/`。
3. **读取生成的文件**,提取关键约束:
   - `config.json` —— 结构化数据:`scope.in_scope`(只测这些域名)、`scope.out_of_scope_domains`、`rules.required_headers`(必须携带的请求头)、`rules.test_accounts`(只允许用的测试账号)、`rules.forbidden`(禁测类型)、`bounties`(赏金)
   - `PROGRAM.md` —— 整理后的可读文档
   - `raw_policy.txt` / `raw_scope.txt` —— 原始文本,约束有疑问时回查
4. **向用户复述关键约束**(scope 域名、必带请求头、测试账号、禁测项),确认后开始测试。
5. **先理解业务,再接触接口**:测试正式启动前,先梳理目标业务模型——核心业务对象(文件/团队/组织/订单/库/席位等)、对象归属关系、权限层级、业务状态转换(分享/转让/升级/移除)。基于业务推理出候选漏洞点(权限判断可能遗漏的位置),之后接触接口时只选消费这些业务数据的接口做验证。**禁止拿到接口清单就逐个调用看响应。**
6. **测试期间严格遵守**:
   - 只测 `in_scope` 内的域名,`out_of_scope_domains` 一律不碰
   - 所有请求带规则要求的请求头(如 `X-HackerOne-Research: <用户名>`)
   - 测试用户数据只用规则指定的测试账号/实体
   - `forbidden` 列表内的测试类型(DoS、暴力破解、社工、无影响的 CORS/header 报告等)不做

## 检查清单(每次初始化后逐项确认)

- [ ] 规则页已抓取(`raw_policy.txt` 非空)
- [ ] scope 页已抓取(`raw_scope.txt` 非空)
- [ ] `in_scope` 域名列表已确认,后续只测这些
- [ ] `out_of_scope` 域名与禁测类型已确认
- [ ] 必带请求头已配置(`X-HackerOne-Research`)
- [ ] 测试账号/实体已确认(如有)

## 约束

- 只测 HackerOne 平台的项目(Intigriti 不在测试范围)
- 先初始化,后测试;切换目标必须重新初始化
- 范围外域名、规则禁测类型,一律不测、不报
- 发现按规则要求写报告(可复现步骤、字数要求、单报告单漏洞)
- 脚本用法与输出说明见 [references/usage.md](references/usage.md)

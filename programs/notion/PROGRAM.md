# notion - 漏洞赏金项目初始化报告

- 平台: hackerone
- 页面: https://hackerone.com/notion
- 抓取时间: 2026-08-12T09:25:56+00:00
- 测试用户名: pccp(用于规则请求头)

## Scope
| 资产 | 类型 | 最高严重度 | 赏金资格 |
|---|---|---|---|
| notion.id | Other | critical | eligible |
| Notion Authentication | Other | critical | eligible |
| mail.notion.so | Domain | critical | eligible |
| Github Repositories or other public artifacts owned by makenotion | Other | critical | eligible |
| calendar.notion.so | Domain | critical | eligible |

## 赏金(从页面提取,含统计值,以规则页为准)
$88、$50、$100、$250、$1,679、$500、$2,000、$5,000、$150、$30,575

## 报告要求
- Please provide detailed reports with reproducible steps. If the report is not detailed enough to reproduce the issue, the issue will not be eligible for a reward.
- Make a good faith effort to avoid privacy violations, destruction of data, and interruption or degradation of our service. Only interact with accounts you own or with the explicit permission of the account holder.

## Out of scope 测试类型(规则禁测)
- Core Ineligible Findings are out of scope.
- Category
- Exclusion details
- Javascript Execution on file hosting domains
- Javascript execution on [file.notion.so](http://file.notion.so) and [notion-static.com](http://notion-static.com) is expected. To be considered in scope, you will need to demonstrate how it harms users on in-scope assets.
- Bypass lock features on page and database views
- Bypasses of lock features on page and database views are out of scope
- Bypassing paywalls on particular features
- Obtaining access to a paid feature of a higher level plan is out of scope
- AI Responses
- Notion leverages frontier models like OpenAI and Anthropic. Engineered prompts to evoke inappropriate responses from the AI is out of scope and should be submitted to model vendors. This includes system prompt disclosures when further impact on users cannot be demonstrated.
- In-App Contact form
- In-App Contact form is out of scope since it is linked to an external platform. Please avoid submitting responses to this form for security testing purposes.
- Other
- Other exclusions detailed in the program description apply
- Platform standards deviations
- This program has not committed to the following Platform Standards. As such the report severity or outcome may differ.
- Severity rating for insecure direct object references (IDORs) with unpredictable IDs
- Multiple reports on systemic vulnerabilities
- Evaluation and payment for bypassing previously resolved vulnerabilities
- Severity rating for vulnerable network connection in client applications
- Responsible disclosure process for third-party component vulnerabilities
- Severity rating for leakage of sensitive personally identifiable information
- Severity rating for vulnerabilities involving a self-sign-up flow
- Third-party components: for programs consuming the component
- Check here for the full Platform Standards page list.
- Exemplary Standards
- This program has committed to awarding the submissions below.
- Bounty awards for discovered leaked credentials
- Check here for the full Exemplary Standards page list.

## 原始抓取文件
- 规则页: `D:\scan\programs\notion\raw_policy.txt`
- Scope页: `D:\scan\programs\notion\raw_scope.txt`
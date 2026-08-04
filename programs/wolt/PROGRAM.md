# wolt - 漏洞赏金项目初始化报告

- 平台: hackerone
- 页面: https://hackerone.com/wolt
- 抓取时间: 2026-08-03T02:27:00+00:00
- 测试用户名: pccp(用于规则请求头)

## Scope
| 资产 | 类型 | 最高严重度 | 赏金资格 |
|---|---|---|---|
| wolt.com | Domain | critical | eligible |
| restaurant-api.wolt.com | Domain | critical | eligible |
| ops.wolt.com | Domain | critical | eligible |
| merchant.wolt.com | Domain | critical | eligible |
| drive.wolt.com | Domain | critical | eligible |
| corporate.wolt.com | Domain | critical | eligible |
| authentication.wolt.com | Domain | critical | eligible |

## 赏金(从页面提取,含统计值,以规则页为准)
$150、$750、$1,500、$3,500、$2,500、$5,000

## 必须携带的请求头
- `X-HackerOne-Research: [H1 username]. Reports resulting in testing without headers can result in the`

## 测试账号/实体
- user_id is 670fa3e9ead6e49d65cc3614
- venue_id is 670e7897e3c56dcc5b5a0989

- https://wolt.com/en/fin/helsinki/venue/test-670e7897e3c56dcc5b5a0989-sh0p

## 报告要求
- Please provide detailed reports with reproducible steps. If the report is not detailed enough to reproduce the issue, the issue will not be eligible for a reward.
- Submit one vulnerability per report unless you need to chain vulnerabilities to provide impact.
- Please, keep report brief and concise. 300-400 words per report is a good limit.

## Out of scope 测试类型(规则禁测)
- Core Ineligible Findings are out of scope.
- Multiple leaked human identity credentials originating from third-party datasets (leaked credential lists, databases, monitoring services and credential marketplaces)
- Testing the payment processors is out of scope
- Spam, social engineering and physical intrusion
- There are humans behind every Customer Support chat. Any interaction with Customer Support staff, including social engineering attempts, is forbidden and out of scope
- Network DoS/DDoS attacks
- Web Cache Poisoned Denial of Service
- Brute force attacks
- Attacks requiring access to a victim's computer/device
- Reports that state that software is out of date/vulnerable without a proof-of-concept
- Mass creating of entities, including accounts, profiles and applications
- GATEKEEPER_API_KEY exposure since it is not a secret value
- API key disclosure without proven business impact
- Signup with unverified mobile numbers (if you took over an existing number, then that's a finding!)
- Verbose messages/files/directory listings without disclosing any sensitive information
- CORS misconfiguration without proven impact
- Missing cookie flags
- Missing security headers
- Cross-site Request Forgery without proven impact
- Autocomplete on web forms
- Bypassing rate-limits or the non-existence of rate-limits
- Best practices violations (password complexity, expiration, re-use, etc.)
- Clickjacking without proven impact/unrealistic user interaction
- CSV Injection
- Sessions not being invalidated (logout, enabling 2FA, etc.)
- Content injection without being able to modify the HTML
- Username/email enumeration
- Email bombing
- HTTP Request smuggling without any proven impact
- Homograph attacks
- Banner grabbing/Version disclosure
- Subdomain takeover without proof
- Arbitrary file upload without proof
- Host header injection without proven business impact
- Shared links leaked through the system clipboard
- Attacks requiring malicious apps to be installed beforehand
- Sensitive data in URLs/request bodies when protected by TLS
- Lack of obfuscation
- Path disclosure in the binary
- Lack of jailbreak & root detection
- Crashes due to malformed URL Schemes
- Lack of binary protection (anti-debugging) controls, mobile SSL pinning
- Snapshot/Pasteboard leakage
- Runtime hacking exploits (exploits only possible in a jailbroken environment)

## 原始抓取文件
- 规则页: `D:\scan\programs\wolt\raw_policy.txt`
- Scope页: `D:\scan\programs\wolt\raw_scope.txt`
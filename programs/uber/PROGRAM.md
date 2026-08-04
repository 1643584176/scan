# uber - 漏洞赏金项目初始化报告

- 平台: hackerone
- 页面: https://hackerone.com/uber
- 抓取时间: 2026-08-04T04:32:46+00:00
- 测试用户名: pccp(用于规则请求头)

## Scope
| 资产 | 类型 | 最高严重度 | 赏金资格 |
|---|---|---|---|
| uber.com | Domain | critical | eligible |
| https://appsec-analysis.uber.com/public/bugbounty/listdomains |  |  |  |
| https://appsec-analysis.uber.com/public/bugbounty/listips | Other | none | eligible |
| *.uberinternal.com | Other | none | eligible |

## Out of scope 域名
- uber.onelogin.com(Domain)
- uber.com.cn(Domain)
- scaledsolutions*.uber.com(Wildcard)
- people.uber.com(Domain)
- newsroom.uber.com(Domain)
- merchants.ubereats.com(Domain)
- love.uber.com(Domain)
- https://brand.uber.com(URL)
- https://assets.uber.com(Other)
- et.uber.com(Domain)
- eng.uber.com(Domain)
- drive.uber.com(Domain)
- central-beta.uber.com(Domain)
- bizblog.uber.com(Domain)
- *scaledsolutions.uber.com(Wildcard)
- *.ubertransit.io(Other)
- *.uberscoot.us(Other)
- *.ubercarshare.com(Other)

## 赏金(从页面提取,含统计值,以规则页为准)
$300、$991、$500、$2,500、$5,904、$4,000、$11,000、$15,000、$700、$3,000、$50,000、$98,248

## 报告要求
- Do be patient & make a good faith effort to provide clarifications to any questions we may have about your submission
- Do respect privacy & make a good faith effort not to change or destroy Uber or personal data
- Test with care: You should never leave a system or users in a more vulnerable state than when you found them. This means that you should not engage in testing or related activities that degrades, damages, or destroys information within our systems, or that may impact our users, such as denial of service, social engineering or spam. If you have made a good faith effort to abide by these Program Terms, we will not initiate or recommend legal action against you, and if a third party initiates legal action, we will make it known that your activities were conducted pursuant to the Bug Bounty Program. Failure to act in good faith will result in immediate disqualification from the Bug Bounty Program and ineligibility for receiving any benefit of the Bug Bounty Program. If at any point while researching a vulnerability, you are unsure whether you should continue, immediately engage with our security team.

## Out of scope 测试类型(规则禁测)
- Core Ineligible Findings are out of scope.
- uber.onelogin.com
- uber.com.cn
- scaledsolutions*.uber.com
- people.uber.com
- newsroom.uber.com
- merchants.ubereats.com
- love.uber.com
- https://brand.uber.com
- https://assets.uber.com
- et.uber.com
- eng.uber.com
- drive.uber.com
- central-beta.uber.com
- bizblog.uber.com
- *scaledsolutions.uber.com
- *.ubertransit.io
- *.uberscoot.us
- *.ubercarshare.com

## 原始抓取文件
- 规则页: `D:\scan\programs\uber\raw_policy.txt`
- Scope页: `D:\scan\programs\uber\raw_scope.txt`
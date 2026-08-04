# instacart - 漏洞赏金项目初始化报告

- 平台: hackerone
- 页面: https://hackerone.com/instacart
- 抓取时间: 2026-08-04T04:31:07+00:00
- 测试用户名: pccp(用于规则请求头)

## Scope
| 资产 | 类型 | 最高严重度 | 赏金资格 |
|---|---|---|---|
| www.instacart.com | Domain | critical | eligible |
| template.uat.foodstorm.com | Domain | critical | eligible |
| shoppers.instacart.com | Domain | critical | eligible |
| com.instacart.client | Android: Play Store | critical | eligible |
| api.instacart.com | Other | critical | eligible |
| admin.instacart.com | iOS: App Store | critical | eligible |
| *.instacart.tools | Wildcard | critical | eligible |
| *.instacart.com | Wildcard | critical | eligible |

## Out of scope 域名
- tech.instacart.com(Domain)
- news.instacart.com(Domain)
- life.instacart.com(Domain)
- instacart.careers(Domain)
- enterprise-status.instacart.com(Domain)
- design.instacart.com(Domain)
- covidresponse.instacart.com(Domain)
- corporate.instacart.com(Domain)
- carrotstore.instacart.com(Domain)
- careers.instacart.com(Domain)
- brand.instacart.com(Domain)
- *.email.instacart.com(Wildcard)

## 赏金(从页面提取,含统计值,以规则页为准)
$172、$50、$250、$719、$1,500、$2,106、$5,000、$6,175、$15,000、$200、$2,500、$20,000、$39,900

## Out of scope 测试类型(规则禁测)
- Core Ineligible Findings are out of scope.
- tech.instacart.com
- news.instacart.com
- life.instacart.com
- instacart.careers
- enterprise-status.instacart.com
- design.instacart.com
- covidresponse.instacart.com
- corporate.instacart.com
- carrotstore.instacart.com
- careers.instacart.com
- brand.instacart.com
- *.email.instacart.com

## 原始抓取文件
- 规则页: `D:\scan\programs\instacart\raw_policy.txt`
- Scope页: `D:\scan\programs\instacart\raw_scope.txt`
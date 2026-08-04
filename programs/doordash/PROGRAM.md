# doordash - 漏洞赏金项目初始化报告

- 平台: hackerone
- 页面: https://hackerone.com/doordash
- 抓取时间: 2026-08-04T04:22:11+00:00
- 测试用户名: pccp(用于规则请求头)

## Scope
| 资产 | 类型 | 最高严重度 | 赏金资格 |
|---|---|---|---|
| www.doordash.com | Domain | critical | eligible |
| doordash.doordashconsumer | iOS: App Store | critical | eligible |
| com.dd.doordash | Android: Play Store | critical | eligible |

## Out of scope 域名
- unified-gateway.doordash.com(Domain)
- track.doordash.com(Domain)
- merchant-portal.doordash.com(Domain)
- merchant-mobile-bff.doordash.com(Domain)
- ir.doordash.com(Domain)
- internal.doordash.com(Domain)
- https://doordash.com/merchant(URL)
- http://help.doordash.com(URL)
- doordash.com/unified-gateway/*(Wildcard)
- doordash.com/orders/drive/*(Wildcard)
- DoorDash Payments(Other)
- consumer-mobile-bff.doordash.com(Domain)
- careersatdoordash.com(Domain)
- *.order.online(Wildcard)
- *.doorcrawl.com(Wildcard)
- *.dashapi.com(Wildcard)

## 赏金(从页面提取,含统计值,以规则页为准)
$50、$100、$724、$500、$1,000、$3,105、$5,000、$12,000、$52,931、$5,700、$21,109

## Out of scope 测试类型(规则禁测)
- Core Ineligible Findings are out of scope.
- unified-gateway.doordash.com
- track.doordash.com
- merchant-portal.doordash.com
- merchant-mobile-bff.doordash.com
- ir.doordash.com
- internal.doordash.com
- https://doordash.com/merchant
- http://help.doordash.com
- doordash.com/unified-gateway/*
- doordash.com/orders/drive/*
- DoorDash Payments
- consumer-mobile-bff.doordash.com
- careersatdoordash.com
- *.order.online
- *.doorcrawl.com
- *.dashapi.com

## 原始抓取文件
- 规则页: `D:\scan\programs\doordash\raw_policy.txt`
- Scope页: `D:\scan\programs\doordash\raw_scope.txt`
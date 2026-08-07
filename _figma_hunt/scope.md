# Figma H1 赏金项目（hackerone.com/figma）

来源: bountyhunte.rs/programs/figma（2026-08-07 获取）
类型: Managed, Offers bounties, $50 minimum
官方重点: "Our primary focus is on high/critical findings right now"
赏金模型: paid, general platform
启动: 2020-04-02, scope 最近变更 2026-07-21

## In Scope (8)
1. Web | https://www.figma.com —— 主要找 high/critical
2. Web | https://api.figma.com
3. Product | Figma Atlassian App (Figma for Jira) https://marketplace.atlassian.com/apps/1217865/figma-for-jira
   —— "Unauthorized access via this app or the APIs that this app uses is also in scope"
4. Product | Figma Desktop App
5. Product | Figma iOS and Android apps
6. Product | Figma Slack App https://figma.slack.com/apps/A01N2QYSA81-figma-and-figjam
7. Product | Figma for Microsoft Teams https://appsource.microsoft.com/en-us/product/office/wa200004521
8. Product | Figma Weave（原 Weavy）—— Figma 应用内 iframe, https://figma.com/weave/... 或 https://weavy.ai/

## Out of Scope (1)
- https://www.designsystems.com

## 变更历史
- 2026-07-21 scope 覆盖变更
- 2026-07-07 in-scope 从 7 扩到 8（+Figma Weave）
- 2026-05-10 资产覆盖变更

## 直连验证（223.5.5.5 DNS + --noproxy）
- figma.com 301 -> www.figma.com (3.173.219.25)
- www.figma.com 200 (3.168.245.54, CloudFront)
- api.figma.com 302 (3.165.11.29, CloudFront)
- static.figma.com 403 (54.239.163.112, S3)
- figma.dev 系无 DNS

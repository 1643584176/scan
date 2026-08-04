# valve - 漏洞赏金项目初始化报告

- 平台: hackerone
- 页面: https://hackerone.com/valve
- 抓取时间: 2026-08-03T02:25:49+00:00
- 测试用户名: pccp(用于规则请求头)

## Scope
| 资产 | 类型 | 最高严重度 | 赏金资格 |
|---|---|---|---|
| www.valvesoftware.com | Domain | critical | eligible |
| www.teamfortress.com | Domain | critical | eligible |
| www.dota2.com | Domain | critical | eligible |
| www.counter-strike.net | Domain | critical | eligible |
| wiki.teamfortress.com | Domain | critical | ineligible |
| support.steampowered.com | Domain | critical | eligible |
| storefront.steampowered.com | Domain | critical | ineligible |
| store.steampowered.com | Domain | critical | eligible |
| steamcommunity.com | Domain | critical | eligible |
| Steam Servers | Other | critical | eligible |
| Steam Client | Other | critical | eligible |
| playartifact.com | Domain | critical | eligible |
| partner.steampowered.com | Domain | critical | eligible |
| partner.steamgames.com | Domain | critical | eligible |
| https://github.com/valvesoftware | Source code | critical | ineligible |
| help.steampowered.com | Domain | critical | eligible |
| com.valvesoftware.Steam | iOS: App Store | critical | eligible |
| com.valvesoftware.Steam | Android: Play Store | critical | eligible |
| api.steampowered.com | Domain | critical | eligible |
| *.steamstatic.com | Wildcard | critical | eligible |
| developer.valvesoftware.com | Domain | low | eligible |

## Out of scope 域名
- www.steampowered.com(Domain)
- www.steamgames.com(Domain)
- valvestore.forfansbyfans.com,store.valvesoftware.com(Domain)
- translation.steampowered.com(Domain)
- list.valvesoftware.com(Domain)

## 赏金(从页面提取,含统计值,以规则页为准)
$100、$200、$750、$1,641、$2,500、$5,679、$7,500、$3,000、$20,000

## 关键约束备注
- Subdomains of listed websites are not in scope unless mentioned
- cookie called 'sessionid.

## 报告要求
- Your report must meet the following requirements to be accepted:
- Actual RCE must be demonstrated. Your report should include clear steps that reliably launch another application - e.g. Calculator - on the target machine.
- Let us know as soon as possible upon discovery of a potential security issue, and we'll make every effort to quickly resolve the issue.
- Make a good faith effort to avoid privacy violations, destruction of data, and interruption or degradation of our service.

## Out of scope 测试类型(规则禁测)
- Core Ineligible Findings are out of scope.
- The following items are considered out-of-scope for all Valve offerings:
- Hypothetical issues that do not have any practical impact. Examples include:
- Vulnerabilities reported by use of automated tools/scanners, without accompanying validation / POC.
- User enumeration without any further impact.
- Clickjacking without a well-defined security/privacy risk.
- Disclosure of software version numbers (we maintain forks of several tools, and apply security patches accordingly).
- Attacks that require social engineering/phishing.
- Attacks that require physical access to the user’s device.
- Attacks that involve the user running malware that then places or modifies content on the target machine, which Steam could later run as the local user.
- However, any case that allows malware or compromised software to perform privilege elevation through Steam, without providing administrative credentials or confirming a UAC dialog, is in scope.
- Additionally, any unauthorized modification of the privileged Steam Client Service is also in scope.
- Open redirects or linkfilter bypasses that cannot be leveraged to programmatically exfiltrate sensitive information (e.g., cookies, OAuth tokens, etc.).
- Content Spoofing / Text Injection that cannot be leveraged for XSS or sensitive data disclosure.
- Host header injection without a specific proof of concept.
- Self XSS, or XSS that only affects out-of-date browsers.
- Denial of Service Attacks.
- Broken links to third party sites.
- Additionally, the following items are out-of-scope for issues with Valve games and related components:
- Attacks that only affect or are only triggered in single-player games that are not caused by a previous multiplayer session (e.g., game files or resources downloaded by a game server).
- Reports against Source Engine tools, e.g. Hammer, Source Filmmaker.
- Reports that require the user to open crafted game content: demo files, BSPs, etc not delivered as part of the exploit.
- While researching, we'd like to ask you to refrain from:
- Denial of service.
- Spamming.
- Social engineering (including phishing) of Valve staff or contractors.
- Any physical attempts against Valve property or data centers.
- www.steampowered.com
- www.steamgames.com
- valvestore.forfansbyfans.com,store.valvesoftware.com
- translation.steampowered.com
- list.valvesoftware.com

## 原始抓取文件
- 规则页: `D:\scan\programs\valve\raw_policy.txt`
- Scope页: `D:\scan\programs\valve\raw_scope.txt`
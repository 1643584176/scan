# Matomo - Rules Baseline

> Program: https://hackerone.com/matomo | Dump date: 2026-09-06 | Researcher: xxbo
> **Policy pages are user-provided: paste the live policy below before testing.**

## 1. Policy (paste from HackerOne policy page)

Known so far (from asset instructions + public sources):
- **matomo.cloud + `$username.matomo.cloud` in scope**; "please limit tests to ones that don't
affect the live instance" + **no automated tools**; Matomo explicitly encourages setting up
YOUR OWN instance for extensive testing (https://matomo.org/docs/installation/).
- Full GitHub orgs matomo-org + innocraft in scope (archived/forked repos excluded).
- Mobile apps (iOS 737216887 / Android org.piwik.mobile2): ONLY critical issues compromising
the token are in scope.
- Out: matomo.org / api.matomo.org / forum (discourse->report to discourse bbp) /
  plugins.matomo.org (marketplace platform) / shop.matomo.org.

```
TODO: paste full policy (rules, eligibility, testing instructions, rewards, exclusions,
known issues list if any)
```

## 2. In-Scope Assets (from bounty-targets dump, verify live)

| Asset | Type | Bounty | Instruction |
|---|---|---|---|
| 737216887 | APPLE_STORE_APP_ID | No | Matomo Mobile 2 iOS App
Only critical issues compromising the token are in scope. |
| https://github.com/innocraft/ | SOURCE_CODE | Yes | All other software on the innocraft GitHub organisation. Archived or forked repositories a |
| https://github.com/matomo-org | SOURCE_CODE | Yes | All other software on the matomo-org GitHub organisation not listed separately. Archived o |
| https://github.com/matomo-org/developer-documentation | SOURCE_CODE | Yes | Developer Documentation. Vulnerabilities are only in scope in case they affect https://dev |
| https://github.com/matomo-org/docker | URL | Yes |  Official Docker project for Matomo Analytics  |
| https://github.com/matomo-org/matomo | SOURCE_CODE | Yes | this repository contains the source code of Matomo Analytics |
| https://github.com/matomo-org/tracker-proxy | SOURCE_CODE | Yes | Matomo Tracker Proxy |
| https://plugins.matomo.org/developer/innocraft | SOURCE_CODE | Yes | Official plugins by Innocraft |
| https://plugins.matomo.org/developer/matomo-org | SOURCE_CODE | Yes | Official plugins by the Matomo team |
| matomo.cloud | URL | Yes | Matomo Analytics Cloud
*$username.matomo.cloud* is also in scope, but please limit tests t |
| org.piwik.mobile2 | GOOGLE_PLAY_APP_ID | No | Matomo Mobile 2 Android App
Only critical issues compromising the token are in scope. |

## 3. Out-of-Scope (from dump; verify live)

| Asset | Type | Instruction |
|---|---|---|
| api.matomo.org | URL |  |
| forum.matomo.org | URL | Please don't post test posts on the forum.
The forum is using discourse, so please report  |
| matomo.org | URL | Project website |
| plugins.matomo.org | URL | The Matomo Marketplace Platform is excluded from this bug bounty |
| shop.matomo.org | URL |  |

## 4. Hard Rules Checklist (fill from policy)

- [ ] Account naming / test-account constraints (cloud instance - H1 alias email?)
- [x] No automated tools on matomo.cloud; own-instance testing explicitly allowed
- [x] Test only own instance / own data ("limit tests to ones that don't affect the live instance")
- [ ] Known-findings / exclusions list reviewed (check CVE history for closed classes)
- [ ] Report requirements (ids, timestamps, headers)
- [ ] Rewards table + severity rationale

## 5. Execution Discipline

- One probe script = one hypothesis + baseline control + single-variable mutations
- Log account/IP/timestamp per report requirement
- Dedupe + impact-first writeup before any submission

## 6. Test strategy (DB/query focus)

1. Local full clone under `_src/matomo` + local docker instance (allowed by policy).
2. Audit query construction: Web API params -> SQL (segments, filter_*, period/date, dimensions).
3. Reproduce locally, then diff behaviour against matomo.cloud (multi-tenant deltas).
4. Respect: no automated tools against matomo.cloud; low volume manual probes only.

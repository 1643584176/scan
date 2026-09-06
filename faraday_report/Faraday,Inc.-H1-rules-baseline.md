# Faraday,Inc. - Rules Baseline

> Program: https://hackerone.com/faraday_inc | Dump date: 2026-09-06 | Researcher: xxbo
> **Policy pages are user-provided: paste the live policy below before testing.**

## 1. Policy (paste from HackerOne policy page)

```
TODO: paste full policy (rules, eligibility, testing instructions, rewards, exclusions)
```

## 2. In-Scope Assets (from bounty-targets dump, verify live)

| Asset | Type | Bounty | Instruction |
|---|---|---|---|
| api.faraday.ai | URL | Yes |  |
| app.faraday.ai | URL | Yes |  |
| buy.faraday.ai | URL | Yes |  |
| gs://faraday-secret | OTHER | Yes |  |
| gs://fdy-production-sdk-uploads | OTHER | Yes |  |
| row.pro | URL | Yes |  |
| s3://faraday-secret | OTHER | Yes |  |
| s3://faraday-uploads | OTHER | Yes |  |
| vault2.faraday.ai | URL | Yes |  |

## 3. Out-of-Scope (from dump; verify live)

| Asset | Type | Instruction |
|---|---|---|
| Support Live Chat | OTHER | Support Live Chat is provided by Hubspot. If you have any security issues to report, use h |

## 4. Hard Rules Checklist (fill from policy)

- [ ] Account naming / test-account constraints
- [ ] Allowed methods / rate limits / no-scanner rule
- [ ] Test only own data; no third-party interaction
- [ ] Known-findings / exclusions list reviewed
- [ ] Report requirements (ids, timestamps, headers)
- [ ] Rewards table + severity rationale

## 5. Execution Discipline

- One probe script = one hypothesis + baseline control + single-variable mutations
- Log account/IP/timestamp per report requirement
- Dedupe + impact-first writeup before any submission

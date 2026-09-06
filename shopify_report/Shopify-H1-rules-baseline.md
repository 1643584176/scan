# Shopify - Rules Baseline

> Program: https://hackerone.com/shopify | Dump date: 2026-09-06 | Researcher: xxbo
> **Policy pages are user-provided: paste the live policy below before testing.**

## 1. Policy (paste full H1 policy below before testing)

Source so far (public, 2026-09-06): shopify.com/ca/bugbounty + getting-started + calculator pages.

- **Max bounty US$200,000 (Critical)**; program paid ~$9.55M total; 2,069 reports / 90d (very active, high competition).
- **Registration for testing**: `https://partners.shopify.com/signup/bugbounty` using the H1 email alias
  (`<h1user>@wearehackerone.com` + plus-addressing). MUST test only stores YOU created; testing live merchants
  => N/A or disqualification.
- **Scoring**: custom calculator - Value Density (depth of impact per exploit), Automatable (full chain unattended),
  Attack Requirements (feature flags/race/state/deployment), Privileges Required, User Interaction
  (None/Passive/Active), Subsequent System Impact (Confidentiality/Integrity/Availability split), Availability (High/Low).
- Environment split Core vs Non-core (non-core rewards calculated differently).
- Scope questions: bugbounty@shopify.com (no vuln discussion over email - H1 only).

```
TODO: paste full H1 policy (rules of participation, known issues list, out-of-scope
vuln types, eligibility, disclosure policy)
```

## 2. In-Scope Assets (from bounty-targets dump, verify live)

| Asset | Type | Bounty | Instruction |
|---|---|---|---|
| *.pci.shopifyinc.com | WILDCARD | Yes |  Environment: Core |
| *.shopify.com | WILDCARD | Yes | Environment: Non-core

Reports involving *.shopify.com are reviewed on a per case basis fo |
| *.shopify.io | WILDCARD | Yes | Environment: Non-core

*.shopify.io may include developer test or third party applications |
| *.shopifycloud.com | WILDCARD | Yes | Environment: Non-core

*.shopifycloud.com may include developer test or third party applic |
| *.shopifycs.com | WILDCARD | Yes | Environment: Non-core

Shopify's service for handling credit card data in a PCI compliant  |
| *.shopifykloud.com | WILDCARD | Yes | Environment: Non-core

Shopify Kloud includes all *.shopifykloud.com applications. Please  |
| Authentication & ATO | OTHER | Yes |  |
| Shopify Developed Apps | OTHER | Yes | Environment: Non-core

Shopify apps and sales channels means everything installed via the  |
| Shopify Mobile Applications | OTHER | Yes | Environment: Non-core

Android: https://play.google.com/store/apps/dev?id=8929232438554100 |
| Shopify Third Party Apps | OTHER | No | Environment: Non-core

Vulnerabilities found in Shopify third party apps should be reporte |
| Shopify Third Party Store | OTHER | No | Environment: Non-core

You may only test against shops you have created. |
| accounts.shopify.com | URL | Yes | Environment: Core |
| admin.shopify.com | URL | Yes | Environment: Core |
| arrive-server.shopifycloud.com | URL | Yes | Environment: Core |
| https://github.com/Shopify/* | SOURCE_CODE | Yes | Environment: Non-core

Public repositories available under the Shopify organization in Git |
| linkpop.com | URL | Yes | Environment: Non-core |
| partners.shopify.com | URL | Yes | Environment: Core |
| shop.app | URL | Yes | Environment: Core |
| shopify.plus | URL | Yes | Environment: Core |
| shopifyinbox.com | URL | Yes | Environment: Non-core |
| your-store.myshopify.com | URL | Yes | Environment: Core

Your development store hosted at `*.myshopify.com`. Create a developmen |

## 3. Out-of-Scope (from dump; verify live)

| Asset | Type | Instruction |
|---|---|---|
| *.email.shopify.com | WILDCARD | Environment: Non-core

Operated by a third party. |
| Other | OTHER | Environment: Non-core
 |
| academy.shopify.com | URL | Environment: Non-core

Operated by a third party. |
| cdn.shopify.com | URL | Environment: Non-core

Shopify allows merchants to upload any file they want on our conten |
| community.shopify.com | URL | Environment: Non-core

community.shopify.com is a third party service and not in scope of  |
| community.shopify.dev | URL | Environment: Non-core

community.shopify.dev is a third party service and not in scope of  |
| investors.shopify.com | URL | Environment: Non-core

Operated by a third party. |
| livechat.shopify.com | URL | Environment: Non-core

Contacting Shopify Support over chat, email or phone about your Hac |
| supplier-portal.shopifycloud.com | OTHER | Environment: Non-core

Includes invoices.shopify.io, factures.shopify.io, invoices.shopify |

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

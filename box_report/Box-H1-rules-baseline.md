# Box BB - Rules Baseline & DB-Attack-Surface Plan

> Program: https://hackerone.com/box_private (Box BB)
> Policy last updated: 2026-08-08 | Scope last updated: 2026-09-02
> Researcher H1 handle: **xxbo**
> Working dir: `box_report/`

## 1. Hard Rules (non-negotiable)

- **Account naming**: primary `xxbo@wearehackerone.com`; extra accounts `xxbo+<id>@wearehackerone.com`; developer accounts `xxbo+dev@wearehackerone.com` / `+dev2` (max 2). NO gmail/other domains.
- **Test only own accounts/data**: no interaction with any enterprise/personal Box account not owned by us.
- **No automated scanners**. Limited automation: low-volume, narrowly targeted, non-disruptive. No mass scanning, no high-volume enumeration, no excessive API use.
- **No DoS**, no disproportionate resource use (storage/bandwidth/AI/signing/messaging/workflow/compute).
- **No malicious software/file upload**; no contact with third parties or non-controlled accounts (no invites/shared links/signature requests/notifications to third parties).
- **Stop & report** if any customer data is stumbled upon; remove from possession.
- **No public disclosure**; all comms through HackerOne only.
- First reporter wins; known/dup issues not eligible.
- Automated scanners prohibited — keep probes manual/low-volume.
- Do not exploit beyond minimum steps needed to demonstrate on own assets.
- **Read-only preference for DB probes**: no destructive payloads on shared state; use own files/folders/metadata only.

## 2. Account Checklist

- [ ] Register personal account at `account.box.com` / app.box.com signup with `xxbo@wearehackerone.com`
- [ ] Request advanced-features upgrade via program Security Page credential management (requires Signal >= 5, Reputation >= 100; ~24h)
- [ ] Create developer app(s) under `xxbo+dev@wearehackerone.com` for OAuth/JWT tokens (max 2)
- [ ] SignRequest test account (`xxbo+SR1@wearehackerone.com`) — **NOT bounty eligible**; staging `sr-staging-1.com` only; `/administrator` on signrequest.com is a honeypot, NEVER visit
- [ ] After upgrade: verify enterprise metadata templates accessible, create own test template

## 3. In-Scope Assets (bounty eligible unless noted)

| Asset | Notes |
|---|---|
| api.box.com | Core API: files/folders/users/collabs/shared links/search/metadata/governance/Shield/events/AI — **primary DB-query surface** |
| app.box.com | Web app incl. Box AI, Shield, Governance, Hubs, Forms, Relay, Notes, Canvas, Admin |
| upload.box.com | Upload pipeline (malware bypass/file parsing) |
| dl.boxcloud.com | Download CDN, signed URLs |
| notes.services.box.com | Notes real-time backend |
| cloud.app.box.com | Cloud-rendered/embedded app views, distinct origin |
| m.box.com | Mobile web |
| account.box.com | Auth plane: OAuth/SSO/tokens/sessions |
| Box Tools / Box Drive / iOS / Android | Desktop/mobile clients |

## 4. DB-Related Focus (per policy "Focus Areas")

SQLi, XML Injection, XSSI, AuthN/Z bugs, Info Disclosure (customer PII/Box data), collaboration-permission bugs. Box AI in scope: cross-user/cross-tenant data access via AI, ACL bypass, prompt injection with security impact, AI acting outside effective permissions.

**Excluded / FP list relevant to us**: info disclosure of non-confidential info (file id, folder id, user id); verbose errors/stack traces alone; username/email enumeration; generic LLM jailbreaks w/o impact; data already accessible under normal permissions.

## 5. Candidate Query Surfaces (to expand from OpenAPI)

1. `POST /2.0/metadata_queries/execute_read` — SQL-like query language (custom parser)
2. `GET /2.0/search` — query, mdfilters, scope, trash, type, sort
3. Box AI endpoints under api.box.com & app.box.com (AI text generation over Box content)
4. Forms / Relay / Notes search & sync query params
5. Events/stream, reports (Admin), metadata templates CRUD, metadata instances
6. XML ingestion surfaces (XXE/XML injection listed in focus) — legacy API? file upload parsers (upload.box.com)

## 6. Execution Discipline

- One probe script = one narrow hypothesis + baseline control + single-variable mutations.
- Everything on own account/data; log account, IP, timestamp per report requirement.
- Before any submission: dedupe check, impact-first writeup (facts vs inference), minimize PoC steps.
- Outcome of every closed question = recorded; unverified closure is not an answer.

# Matomo Query Audit Log

Progress tracking for Matomo H1 bug bounty (audit + local replication).

## Environment: LOCAL INSTANCE (2026-09-06) — DONE

### Services (schtasks "matomoLocalSvc", detached, survive agent console closes)
- **MariaDB 11.4.13** @ 127.0.0.1:3307 — db `matomo`, user `matomo`/`matomo`
  - data dir: `F:\scan\matomo_report\_runtime\mariadb\data`
  - log: `F:\scan\matomo_report\_runtime\mariadb\mariadbd.log`
  - **general log ON** -> `F:\scan\matomo_report\_runtime\mariadb\matomo_general.log`
- **PHP 8.3.33** built-in server @ http://127.0.0.1:8080 (docroot `_src\matomo-release\matomo`)
  - log: `F:\scan\matomo_report\_runtime\php_server.log`

### Instance (Matomo 5.13.0 release, installed via web installer automation)
- Base URL: http://127.0.0.1:8080/
- **admin** (superuser) `M@tomoLocalTest!2026` / xxbo+matomo@wearehackerone.com
  - app token: `c3bf071d7f0db740a6f4c60c6affcfd5`
- **site1** "Local Test Site" (http://127.0.0.1:8080/) — idsite=1
- **site2** "Site Two" (http://site2.local) — idsite=2
- **user2** (view on site2 only) `User2@LocalTest!2026` — app token: `794beeb243443742f0df05b4432c734e`
- **user3** (no access anywhere) `User3@LocalTest!2026` — app token: `bfb52eb146d39b0d40c365a46491f589`
- config: `_src\matomo-release\matomo\config\config.ini.php` (installation_in_progress removed, salt set)

### Installer quirks learned (for reuse)
- Web installer steps driven by HTTP forms, NOT the Vue shell: GET action page -> parse real `<form>` -> POST exact field values.
- CRITICAL: checkbox fields must post real value `1`; submit button must carry exact translated value (`Next »` / `Continue »`); bare `Next` fails silently -> server re-renders welcome.
- Each step requires a warm GET in the SAME cookie session first (fresh-session POST to a later step silently renders welcome).
- `host` field accepts `127.0.0.1:3307` (HostPortExtractor).
- databaseSetup writes config; tablesCreation (auto on GET) creates 34 tables; setupSuperUser creates admin; firstWebsiteSetup creates site (302 to trackingCode w/ site params); finished POST removes `installation_in_progress`.
- Login form fields: `form_nonce` (id=login_form_nonce), `form_login`, `form_password`, `form_rememberme`.
- Matomo 5.x: token_auth moved to table `matomo_user_token_auth`; API `UsersManager.createAppSpecificTokenAuth` requires `passwordConfirmation` (own password) and only works for own account (superuser cannot mint for others).
- API auth works with `token_auth` query param OR web session cookie.

## Static audit status (5.x-dev @ _src\matomo + release 5.13.0 @ _src\matomo-release\matomo)

### Baseline facts (verified SAFE on 5.x-dev branch)
- Segment field names: hard whitelist via SegmentsList (unregistered -> "not a supported segment").
- Segment values: bound `?` placeholders; LIKE escaped (%/_) via escapeLikeString.
- TableLogAction: `(int)` casts + bind; subquery templates sprintf %s for columns only.
- Live/Model, CustomDimensions Dao\Configuration: parameterized everywhere.
- DataTableGenericFilter: filter_* acts on in-memory DataTable only (not SQL).
- 5.x removed array-form sqlFilter registrations; filters live on Dimension objects (19 defs).

### Release 5.13.0 API method census (fresh enumeration)
- 233 public methods across plugins/*/API.php; 96 with explicit check keywords; **137 without**.
  -> full list: `_probes\_nocheck_methods.json`
- Runtime verification plan (todo mt06): call no-check methods as user3 (zero access) and user2 (site2 view only) with idSite=1 (foreign), compare against admin baseline. Look for data leakage / foreign-site reads. Watch general SQL log for queries lacking site-scope conditions.

### mt06 runtime matrix RESULTS (2026-09-06)
- **Archiving deadlock root cause**: single-thread PHP built-in server + Matomo browser-triggered
  archiving falls back to non-async HTTP self-request (CliMulti::executeNotAsyncHttp -> curl to
  own URL) -> self-deadlock, request hangs forever.
  Fix: config `[General] browser_archiving_disabled_enforce = 1` + CLI `console core:archive
  --url=http://127.0.0.1:8080` for manual archiving. API stays fast; data archived OK
  (site1=3 visits, site2=2 visits, 2 conversions readable by admin).
- **Management 53 methods (admin/user2/user3, idSite=1)**: all runtime-guarded correctly.
  - user2/user3 cross-site ops on real TagManager containers -> 401 view-access; user2 own-site
    write -> 401 tagmanager_write capability; addContainer admin baseline OK.
  - TagManager plugin must be activated via `console plugin:activate TagManager`.
  - getFollowingPages (Overlay) returns 200 [] for everyone INCLUDING anon: it swallows the
    Transitions view-access exception (catch -> empty DataTable); inner Transitions API DOES
    checkUserHasViewAccess -> no leak.
  - API.getBulkRequest (5.13 hardened): nested request auth must match root context;
    force_api_session conflicts rejected; anon+nested admin token == direct token use (no lift).
  - Public/no-impact DATA (anon OK): getSettings, getPagesComparisonsDisabledFor,
    LanguagesManager.*, getIpsForRange (CIDR math only), Overlay.getTranslations.
- **Report methods sample (14 methods x idSite 1+2, 3 roles)**: user3 all DENIED(view); user2
  DENIED on idSite=1, DATA on own idSite=2; admin full data. => public check layer guards
  no-check report methods too. CONCLUSION: no-check census does NOT imply missing authz
  (checks live in base class/capability/model layer).
- Remaining for full closure: full report matrix (all ~100 idSite methods), SQL general-log
  scope diff (admin vs user3), param-shape mutations (segment/period/filter_*).

## Attack-surface ledger (open items)
1. ~~API->model chains among 137 no-check methods~~ -> runtime matrix disproved authz gap (mt06, see above)
2. Segment + dimension filters on Live/VisitsSummary/Events APIs (runtime diff with SQL log)
3. tracker-side params (v63-era: idsite override?) - re-check on 5.13
4. matomo.cloud deltas (no account; skip unless H1 creds)
5. ~~Double-user cross-site IDOR matrix (user2 view site2 -> call site1 methods)~~ -> all DENIED
6. FULL report matrix (all ~100 idSite methods x 3 roles x idS 1/2) for closure evidence
7. SQL general-log scope diff: same request admin vs user3 -> column-level scope differences
8. Param-shape mutations: idSite=all/comma/list, segment injection, period/date range abuse

## Next actions
- [x] mint tokens for user2/user3 (login each, createAppSpecificTokenAuth)
  - user2 login OK (200, lands CoreHome idSite=2); user3 login lands 401 page (no-site user, session still valid)
  - createAppSpecificTokenAuth requires own password; superuser CANNOT mint for others (error confirms)
- [x] run no-check API method matrix as user3/user2 vs admin (mgmt 53 + TagManager 35 + report sample) -> all guarded
- [x] seed visit data (tracker) into site1+site2 -> site1=3 visits/1 conv, site2=2 visits/1 conv; archiving via CLI
- [ ] FULL report matrix (remaining ~86 no-check report methods x 3 roles x idS 1+2)
- [ ] diff general SQL log: same request as admin vs user3 -> column-level scope differences

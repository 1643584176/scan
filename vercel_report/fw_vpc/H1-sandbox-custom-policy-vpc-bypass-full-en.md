# Vercel Sandbox "custom" Network Policy: Unintended Allow of Entire Private Address Space (Firewall Bypass)

**Asset**: Vercel Sandbox (https://vercel.com/docs/sandbox)
**Severity**: MEDIUM
**Weakness**: CWE-284 (Improper Access Control)
**Vulnerability class**: Networking and Firewall

## Submission details

- Vercel Team ID: team_GIy1SZ444lspqeNbh4r8uAUg
- Vercel Project ID: prj_iyw2xfjP3RKPT7n8b8c1tBIxxK5F
- Vercel Sandbox ID: sbx_bXiZHfWkprtWEqcK8lp05VPjM4zS (allowcmp, same-sandbox policy-switch control) / sbx_hZ2QLI6yXmdaUUz139Ml8cXzncF3 (fwcustom5, extended sampling) / sbx_q5JMSKybnLoT5G8JcUv1AMMFv8I3 (denyall3, deny-all control)
- PoC zip: fw_vpc_poc.zip (guest repro script fw_mini_guest.py + all 4-phase / extended sampling raw outputs)
- Severity rationale: aligned with bounty table Medium tier "Firewall policy violation without secret exfil (reaching a destination that should have been denied)" — custom mode (documented as deny-by-default) actually allows outbound TCP to the entire AWS VPC private range 172.31.0.0/16 on any port, while the same sandbox in allow-all (default, most permissive) mode cannot reach that range (EHOSTUNREACH); undocumented network-policy violation. No authentication performed, no data read, no exfil demonstrated, therefore not High.
- I have read and accept the severity-inflation penalty terms; Vercel triage decides by maximum provable impact.

## Summary:

Vercel Sandbox `custom` network policy mode (docs: "User-defined policies deny traffic by default and let you allow specific destinations") accidentally allows the **entire private/reserved address space** when permitting VPC DNS: 10.0.0.0/8, 172.16.0.0/12 (incl. tested 172.31.0.0/16), 192.168.0.0/16, 100.64.0.0/10 (CGNAT), 169.254.0.0/16 (link-local) — any IP, any port, TCP all reachable, while the **same sandbox** in default `allow-all` and in `deny-all` modes cannot reach these ranges (EHOSTUNREACH errno 113).

**Three-mode same-sandbox comparison (key evidence)**:

| Policy mode | Private/reserved ranges TCP (sampled 10/8, 172.16/12, 192.168/16, 100.64/10, 169.254/16) | 172.31.0.3:5432 (PG SSLRequest) |
|---|---|---|
| allow-all (default) | all OSERR:113 unreachable (cidr2, 15/15) | OSERR:113 unreachable |
| **custom (allowedDomains=["httpbin.org"])** | **all OPEN (cidr1, 15/15)** | **OPEN, returns b'S' (PG handshake)** |
| deny-all | all OSERR:113 unreachable (denyall3) | OSERR:113 unreachable |
| custom (re-applied) | all OPEN | OPEN, returns b'S' (reproducible) |

**Reachability mapping** (custom mode, cidr1 sandbox): 5 reserved ranges × 3 random IPs × random ports = 15/15 TCP connect success; 5432 on random IPs of every range returns PG SSLRequest response b'S' (incl. 10.107.229.181, 100.124.43.21, 192.168.112.196, 169.254.82.21); port 53 connect success everywhere. Public controls (8.8.8.8 / 1.1.1.1 / 54.172.31.170:443): in custom mode plaintext HTTP is RST'd (DPI filters by SNI), in allow-all it passes through (cloudflare/awselb 400 responses).

**Nature of the 5432 response**: any private IP:5432 returns b'S', TLS ClientHello then EOF, plaintext StartupMessage then RST (fw_pg_fp/fw_pg_tls) — judged to be the firewall's explicit PostgreSQL-protocol handling/proxy response (docs: "Postgres protocol handshake is handled by the firewall"), not a large number of real PG servers in the ranges. No real business-service responses found in the private ranges (plaintext HTTP→RST, SSH/MySQL/Redis banner→NODATA).

**Core conclusion**: custom policy mode allows arbitrary TCP to the entire private/reserved address space (likely a DNS-allow rule accidentally widened to the full RFC1918/reserved space), giving the sandbox a *larger* network reach than the default allow-all mode and violating the documented "deny by default" semantics of custom mode — a sandbox firewall bypass (in-scope: defeating the sandbox firewall to reach unauthorized destinations).

**Aggravating factor (deniedCIDRs ineffective — silent fail-open)**: attempting to narrow the exposure with `deniedCIDRs` fails completely for private/reserved ranges: API accepts the config (200), readback confirms it is saved (`{"deniedCIDRs": ["172.31.0.0/16", ...]}`), no error at all — yet traffic is still allowed. The same field works correctly for public IPs (deny `3.234.68.0/24` → curl to that range fails). The leaked private-range reach **cannot be narrowed with any documented policy field**; the only "effective" mitigation is switching the whole mode to deny-all/allow-all (the documented granular approach is ineffective).

**Attribution (allowedCIDRs works; excludes "all fields broken")**: same sandbox, stepwise — `custom` empty policy → everything blocked (docs "behaves as deny-all" ✓); `allowedCIDRs:["8.8.8.0/24"]` → out-of-allowlist IP (1.1.1.1:53) rejected at TCP layer errno 113 ✓, in-allowlist IP reachable ✓; allow+deny same range → deny wins errno 113 ✓ (docs "Denied ranges take precedence" holds for public IPs). **Decisive reversal (reproduced, npol1 sandbox, three sequential phases)**: `allowedCIDRs:["172.31.0.0/16"]` (the documented way to allow private networks) → 172.31.0.2:5432 **errno 113 unreachable** (Hobby has no Secure Compute, explicit private CIDR does not take effect); same session switched back to `allowedDomains:["httpbin.org"]` → 172.31.0.2:5432 **PG b'S' reachable** (reproduced); then deniedCIDRs scenario → still reachable. The private-range exposure is not the result of any explicit configuration — it is an unintended side effect of the domain-allow path, and the documented explicit private-CIDR path is broken.

## Steps To Reproduce:

1. Create a Vercel Sandbox (Hobby plan, any project); set the network policy via API:
   ```
   POST /v2/sandboxes/sessions/{sid}/network-policy
   {"mode": "custom", "allowedDomains": ["httpbin.org"]}
   ```
2. Inside the sandbox run (Python minimal repro; TCP connect + 8-byte PG SSLRequest only, no auth, no data read):
   ```python
   import socket, struct
   pg = struct.pack('!II', 8, 80877103)          # PG SSLRequest
   s = socket.socket(); s.settimeout(2.5)
   s.connect(('172.31.0.3', 5432))
   s.sendall(pg)
   print(s.recv(8))                              # -> b'S'  (PG SSL handshake response)
   ```
   Observed: `OPEN DATA=b'S'`
3. Switch the same sandbox to allow-all (`{"mode": "allow-all"}`), repeat step 2:
   Observed: `OSERR:113` (EHOSTUNREACH)
4. Switch back to custom, repeat step 2: `OPEN DATA=b'S'` (reproducible; 4-phase log attached)
5. Extended checks (custom mode):
   - Full private-range sampling: 10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16, 100.64.0.0/10, 169.254.0.0/16 × random IP × random port → 15/15 TCP connect success (attached cidr1)
   - allow-all control: same script, same random seed → 15/15 OSERR:113 (attached cidr2)
   - 172.31.0.0/24 full segment × 14 ports: 35 IPs return b'S' on 5432 (attached fw_custom4b)
   - 25 random subnets × 5 IPs = 125/125 sampling all return b'S' (attached fw_vpc_deep)
   - deny-all control: all OSERR:113 (attached denyall3)
6. **Mitigation attempt (deniedCIDRs ineffective, npol1 sandbox, readback-confirmed)**:
   a. `{"mode":"custom","allowedDomains":["httpbin.org"],"deniedCIDRs":["172.31.0.0/16"]}` → 200 saved, readback confirms; sandbox probe 172.31.0.2:5432 → `b'S'` (identical to no-deny baseline; deny not enforced)
   b. `{"mode":"custom","allowedDomains":["httpbin.org"],"deniedCIDRs":["172.31.0.0/16","10.0.0.0/8","100.64.0.0/10","192.168.0.0/16","169.254.0.0/16"]}` → 200 saved, readback confirms all; probes 172.31.0.2 / 10.0.0.2 / 192.168.0.2:5432 → all `b'S'` (deny not enforced)
   c. Field-works control: same sandbox `deniedCIDRs:["3.234.68.0/24"]` (public httpbin IP range) → readback confirms; curl --resolve httpbin.org:443:3.234.68.252 → FAIL (deny works for public IPs)
   d. deny-all control: probe unreachable (errno 113) — only whole-mode switch blocks the private ranges
7. **Attribution (allowedCIDRs works; explicit private CIDR reversal)**:
   a. `{"mode":"custom"}` (empty) → curl httpbin.org FAIL (docs "A user-defined policy with no allowed domains or CIDR ranges behaves as deny-all" ✓)
   b. `{"mode":"custom","allowedCIDRs":["8.8.8.0/24"]}` → 8.8.8.8:53 TCP reachable; 1.1.1.1:53 → errno 113 (out-of-allowlist IP rejected at TCP layer ✓)
   c. `{"mode":"custom","allowedCIDRs":["8.8.8.0/24"],"deniedCIDRs":["8.8.8.0/24"]}` → 8.8.8.8:53 → errno 113 (deny wins for public IPs ✓)
   d. **`{"mode":"custom","allowedCIDRs":["172.31.0.0/16"]}` (documented explicit private-CIDR config) → 172.31.0.2:5432 → errno 113 unreachable** — explicitly allowing the private range makes it unreachable, while a pure public-domain allow makes the whole private space reachable → the exposure is an unintended side effect of the domain-allow path, not of any explicit config
   e. **Reversal re-run confirmation** (second session, same sandbox): A: `allowedDomains:["httpbin.org"]` → PG b'S'; B: `allowedCIDRs:["172.31.0.0/16"]` → PG errno 113; C: back to `allowedDomains` → PG b'S' (reproduced); D: deny-all → errno 113 — three-phase control stable, excludes timing/environment factors

## Supporting Material/References:

Same-sandbox 4-phase switch (allowcmp, same sandbox, same target IP:port, only policy changes):

* P1 allow-all: T1 172.31.0.3:5432 -> OSERR:113; T4 httpbin.org:443 -> OPEN(awselb 400)
  `{"data":"[..] T1 172.31.0.3:5432 -> OSERR:113\n[..] T4 httpbin.org:443 -> OPEN DATA=b'HTTP/1.1 400 Bad Request\\r\\nServer: awselb'"}`
* P2 custom: T1 -> OPEN DATA=b'S'; T4 httpbin.org:443 -> RST (plaintext HTTP without SNI rejected by DPI, consistent with docs "Plain-text HTTP cannot be filtered by domain")
  `{"data":"[..] T1 172.31.0.3:5432 -> OPEN DATA=b'S'\n[..]"}`
* P3 deny-all: all OSERR:113 (incl. DNS 172.31.0.2:53)
  `{"data":"[..] T1 172.31.0.3:5432 -> OSERR:113\n[..] T2 172.31.0.2:53 -> OSERR:113\n[..]"}`
* P4 custom (again): T1 -> OPEN DATA=b'S' (reproduced)
  `{"data":"[..] T1 172.31.0.3:5432 -> OPEN DATA=b'S'\n[..]"}`

Extended sampling (custom mode):

* cidr1: private-range mapping: 10/8, 172.16/12, 192.168/16, 100.64/10, 169.254/16 × random IP:random port = 15/15 OPEN; random IP:5432 of every range all b'S', :53 all OPEN
* cidr2: allow-all control: same script same seed 15/15 OSERR:113; public plaintext HTTP passes (cloudflare/awselb 400)
* http_probe: custom private-range real-service differentiation: plaintext HTTP GET → RST (DPI), SSH/MySQL/Redis banner → NODATA (blackhole, no real service response)
* fw_custom4b: 172.31.0.0/24 × 14 ports, 35 IPs' 5432 returns `DATA b'S'` (172.31.0.3/4/17/18/26/27/34/38/61/72/78/80/81/82/87/94/100/101/109/116/120/125/138/140/150/156/171/181/193/200/203/205/215/226/241)
* fw_vpc_deep: 12 samples all `SSL_OK S`; sandbox-characteristic ports (23456/26661/30002/33090/34121) on 8 IPs all RST (targets are not other tenants' sandboxes); extended sampling **125/125 PG_FOUND b'S'** (172.31.57/140/71/44/16/111/13/214/142/81/174/110/1/2/10/20/30/50/60/90/100/150/200/220/250 subnets)
* fw_pg_fp: plaintext StartupMessage -> RST 9/9 (PG requires TLS or DPI interception)
* fw_pg_tls: TLS ClientHello -> EOF 9/9 (TLS handshake cannot complete, unauthenticated)

Controls (unreachable baseline):

* denyall3 (deny-all): 172.31 whole range OSERR:113, 0 open ports, httpbin/8.8.8.8 all blocked
* fw_custom3 allow-all: 172.31.0.2 all ports + 12 random-IP sampling all OSError
* fw_custom3 custom: 172.31.0.2 all ports (22/80/443/3306/5432/6379/8080/9090/23456/26661/30001/30002/33090/34121/50000/60000) all OPEN; 12 random-IP sampling all OPEN

Official documentation (https://vercel.com/docs/sandbox/concepts/firewall):

* "User-defined policies deny traffic by default and let you allow specific destinations"
* "Plain-text HTTP cannot be filtered by domain, and must be allowed by IP range instead"
* "A user-defined policy with no allowed domains or CIDR ranges behaves as deny-all"
* "Allowed address ranges: ... Use address ranges for non-encrypted traffic or **private network access through Secure Compute**" (private-network access requires explicit CIDR + Secure Compute)
* "When a policy has allow rules, domain and address range rules apply independently. Domain rules do not narrow the IP addresses allowed by subnets.allow."

SDK Reference (https://vercel.com/docs/sandbox/sdk-reference):

* `updateNetworkPolicy({allow: ["google.com", ...]})` → comment "**Allow traffic to specific websites only**" (domain-only allowlist)
* private-network access requires explicit addition: `subnets: { allow: ["10.0.0.0/8"] }` (comment "Allow traffic to specific websites **and private network**") — **the docs explicitly distinguish: a domain-only allowlist ≠ private-network allow**

Official blog (https://vercel.com/blog/a-sandbox-without-a-network-boundary-is-only-half-a-sandbox):

* "Reach a private service, **while blocking the rest of the private address space**"
* "granular policies that **deny unmatched traffic by default**"
* "The firewall ... checks that hostname against the sandbox's domain policy **and also checks the destination address against its CIDR policy**" (every connection passes the CIDR check — the tested deniedCIDRs behavior on private ranges directly contradicts this)
* domain-only allow example policy: "**Other destinations are denied by default**"
* fundamental property of the execution environment: "Which private address ranges are unavailable?"

Firewall docs, denied ranges:

* "**Denied ranges take precedence over allowed domains and address ranges**" (deny beats allow — not true for private ranges: deny+allow configured together still allows private ranges)

Secure Compute (https://vercel.com/docs/networking/secure-compute):

* Secure Compute is **Enterprise-only** (dedicated private network + VPC peering, requires explicit creation and project attachment); the tested account is Hobby, no Secure Compute network configured — excludes "private-range allow comes from Secure Compute"

**Documentation-compliance conclusion**: the tested policy is domain-only `allowedDomains=["httpbin.org"]` (no subnets.allow); docs promise only that domain is allowed ("deny traffic by default" + "specific websites only"), but the implementation allows the entire private/reserved space — **directly contradicts the three official statements; not documented behavior; Out-of-scope #4 (documented limitations) does not apply** — the docs actually require explicit subnets.allow for private-network access, which was not configured.

## Impact:

- **Firewall policy semantics broken**: choosing custom mode (expecting "deny by default, allow only specified domains") yields a *larger* network reach than default allow-all — the entire private/reserved address space (10/8, 172.16/12, 192.168/16, 100.64/10, 169.254/16), any IP, any TCP port, reachable. Actual behavior is the opposite of the documented promise.
- **Internal-reach surface widened**: sandbox can connect to arbitrary private-network IPs and ports; 5432 (PG protocol proxy response b'S') and 53 reachable everywhere; any real business services in these ranges (AWS VPC resources, Vercel production network, future tenant resources) become directly touchable.
- **IMDS/MMDS surface exposed**: 169.254.169.254:80/443 TCP-reachable in custom mode (errno 113 in allow-all); currently no data (Vercel does not serve IMDS content), but the link-local metadata isolation is already bypassed.
- **Potential cross-tenant/production risk**: if 10/8, 172.16/12 etc. carry Vercel production services or other tenants' resources (cross-VPC peering, shared services), sandbox users can reach them (no real service responses found inside the private ranges in this test, but reachability itself is established).
- **Data-exfiltration protection void**: operators relying on custom policy to restrict sandbox egress (e.g. blocking internal/sensitive ranges) do not get the promised protection.
- **Mitigation fully broken (silent fail-open)**: docs promise "Denied ranges take precedence over allowed domains and address ranges"; tested `deniedCIDRs` is not enforced for private/reserved ranges (172.31.0.0/16, 10.0.0.0/8, 192.168.0.0/16 etc.) — API 200, readback normal, no error; operators cannot narrow the exposure; the only pre-fix mitigation is abandoning custom mode for deny-all (losing all allow capabilities).
- **Audit/compliance risk**: because the policy "saves successfully" with normal readback, tenants relying on policy audit (e.g. compliance records of deniedCIDRs) will believe protection is active while it is not.
- **Documented configuration direction fully broken**: following the docs to explicitly set `allowedCIDRs:["172.31.0.0/16"]` ("Use address ranges for ... private network access") yields errno 113 (unreachable), while a pure domain allow with no private-range config accidentally yields whole-range private reach — users cannot "obtain" private access via the documented path (Secure Compute is Enterprise-only) but "accidentally" obtain it via a pure domain policy; configuration semantics and actual behavior are fully disconnected.

Compliance note: all verification used TCP connect + protocol handshake fingerprints (PG SSLRequest 8B / TLS ClientHello / plaintext HTTP GET / SSH/MySQL/Redis banner); no authentication, no data read, no state written. Impact is assessed on reachability and handshake responses.

Suggested fix: narrow the custom-mode internal allow rule from the entire private/reserved space to only VPC DNS (e.g. 172.31.0.2:53) or exact allowlist matches; enforce deniedCIDRs/allowedCIDRs consistently on private ranges as on public IPs; investigate the root cause of the allow-all vs custom reachability difference (likely a DNS-allow route inserted by custom mode accidentally covering the full RFC1918/reserved space).

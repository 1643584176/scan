# Vercel Sandbox "custom" Network Policy: Entire Private Address Space Reachable (Firewall Bypass)

**Asset**: Vercel Sandbox | **Severity**: MEDIUM | **Weakness**: CWE-284 | **Class**: Networking and Firewall

## Summary

`custom` network policy (docs: *"User-defined policies deny traffic by default"*) with only `allowedDomains:["httpbin.org"]` unexpectedly allows **outbound TCP to the entire private/reserved address space** (10/8, 172.16/12 incl. 172.31.0.0/16, 192.168/16, 100.64/10, 169.254/16) on any IP:port. The **same sandbox** shows these networks **unreachable (errno 113) in `allow-all` and `deny-all`** modes — the "strictest" mode grants a *larger* egress surface than the default:

| Policy (same sandbox) | Private-range probes | 172.31.0.3:5432 (PG SSLRequest) |
|---|---|---|
| allow-all | 15/15 errno 113 | errno 113 |
| **custom** | **15/15 OPEN** | **b'S'** (PG handshake) |
| deny-all | 15/15 errno 113 | errno 113 |
| custom (again) | 15/15 OPEN | b'S' (reproduced) |

Extended: 125/125 172.31.x.y:5432 → b'S'; 172.31.0.0/24×14 ports → 35 IPs b'S'. DNS (172.31.0.2:53) is answered by the firewall itself (rcode=5 REFUSED), so private-range allow is not needed for DNS.

**Aggravating**: `deniedCIDRs` for private ranges is **accepted (200) + readback-confirmed but silently not enforced** (fail-open); same field works for public IPs. Operators cannot narrow the exposure by any documented field.

**Attribution (reproduced)**: `allowedCIDRs:["172.31.0.0/16"]` (documented way) → **errno 113**; back to `allowedDomains` → b'S'. Exposure is an unintended side effect of the domain-allow path; the documented CIDR path doesn't work.

## Steps To Reproduce

1. Create a sandbox; set policy: `POST /v2/sandboxes/sessions/{sid}/network-policy` `{"mode":"custom","allowedDomains":["httpbin.org"]}`
2. In sandbox (TCP connect + 8B PG SSLRequest only, no auth/data):
   ```python
   import socket, struct
   s = socket.socket(); s.settimeout(2.5)
   s.connect(('172.31.0.3', 5432))
   s.sendall(struct.pack('!II', 8, 80877103))
   print(s.recv(8))   # -> b'S'
   ```
3. Switch same sandbox to `allow-all` → `OSERR:113`; back to custom → `b'S'` (reproducible).
4. Apply `deniedCIDRs:["172.31.0.0/16",...]` → 200 + readback OK, probes still `b'S'`; control `deniedCIDRs:["3.234.68.0/24"]` (public) → connections fail.

## Supporting Material

- 4-phase same-sandbox switch logs (allowcmp P1–P4), cidr1/cidr2 (15/15 vs 113), fw_custom4b (35 IPs), fw_vpc_deep (125/125), denyall3, mmds1 (DNS REFUSED)
- Attribution: nline_evidence/ (_x_nfinal4, _x_nmulti, _x_nmatrix, _x_cidr, _x_e5repro) + PoC zip fw_vpc_poc.zip

**Doc conflicts (not documented behavior)**: "deny traffic by default" / SDK "Allow traffic to specific websites **only**" / blog "blocking the rest of the private address space" / "Denied ranges take precedence" — all contradicted. Secure Compute (Enterprise-only) not configured → excluded.

## Impact

- `custom` mode grants larger egress than `allow-all`: all private/reserved ranges reachable, incl. link-local (169.254.169.254).
- Any real services in these ranges (production/tenant resources) become reachable from custom-policy sandboxes.
- Exfiltration protection void for operators relying on `custom`; `deniedCIDRs` silently fails → audit/compliance records show protection that doesn't exist.
- Documented private-access path (`allowedCIDRs`) broken; undocumented side effect works — config semantics disconnected.

**Compliance**: TCP connect + handshake fingerprints only; no auth, no data read, no state changes; own account/sandboxes; <5qps. No real service responses found in private ranges (firewall-layer responses only) — impact shown at connectivity/policy level.

## Suggested Fix

Narrow custom-mode internal allow to the VPC DNS endpoint only (or exact allowlist matches); enforce `deniedCIDRs`/`allowedCIDRs` consistently on private ranges; fix the domain-allow path inserting a route covering all RFC1918/reserved space.

**Team ID**: team_GIy1SZ444lspqeNbh4r8uAUg | **Project ID**: prj_iyw2xfjP3RKPT7n8b8c1tBIxxK5F | **Sandbox IDs**: allowcmp / fwcustom5 / denyall3 | Severity rationale aligns with bounty table Medium tier ("Firewall policy violation without secret exfil"); aware of severity-inflation penalty.

## Triage Status (2026-08-30)

Closed as **duplicate of #3951926**. Vercel response: the root cause is that flows authorized by a domain allow rule are not validated against the connection's destination IP, so IP-level denies (deniedCIDRs / subnets.deny entries and the built-in private-range guard) are not enforced on domain-authorized flows. The plain `allowedDomains` form in this report is another way to reach the same missing destination-IP check; single-domain, wildcard, and hostname-resolving-to-private-IP variants were already reported and folded into the same root cause. First reported 2026-08-19; per program policy only the first valid, fully reproducible report of a root cause is rewarded.

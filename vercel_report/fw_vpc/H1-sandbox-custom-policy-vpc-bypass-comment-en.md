# H1 Comment Draft — Additional Evidence for Vercel Sandbox Network Policy Bypass

Paste this as a comment/update on the submitted report (H1-sandbox-custom-policy-vpc-bypass). Keep it as-is or trim to your preferred length.

---

## Update: The bypass is not limited to port 5432 — custom-mode egress exposes the entire VPC-internal network

Following up on the original report, I gathered additional evidence. All tests were performed on my own sandbox project (team_GIy1SZ444lspqeNbh4r8uAUg / prj_iyw2xfjP3RKPT7n8b8c1tBIxxK5F) with plain TCP connect probes (no data exchanged beyond the PostgreSQL SSL-negotiation banner already shown).

### 1. Full VPC-internal reachability (accept-all, not a per-port allowlist)

In a sandbox created with `networkPolicy: {mode: "custom", allowedDomains: ["httpbin.org"]}`:

- TCP connect to **172.31.0.1 (VPC gateway), 172.31.0.2, 172.31.0.3, 10.0.0.2** across **58 ports** (22, 53, 80, 443, 3306, 5432–5439, 6432, 6543, 6379, 8008, 8080–8081, 8443, 8888, 9000, 9090, 9100, 9200, 9300, 2375–2376, 2379–2380, 27017, 28017, 11211, 15672, 5672, 4369, 25672, 10250, 6443, 9092, 2181, 8500, 8300, 8600, 4646–4647, 3000, 5000, 7000–7001, 25060–25061, 8086–8087, 9419, 4444, 7002) → **all 232 connections accepted (SYN-ACK)**.
- Real service confirmed on 172.31.0.2 / 172.31.0.3 / 10.0.0.2 : 5432 — PostgreSQL SSL-negotiation response `S` (as in the original report). All other open ports are firewall "blackhole" accepts (connection established, no data), i.e. the firewall effectively accepts **any** destination port in the VPC-internal range.

### 2. The environment is confirmed as an AWS VPC (real EC2 hosts)

- `/etc/resolv.conf` inside the sandbox: `nameserver 172.31.0.2` (marked `#MANUAL`).
- UDP DNS queries to 172.31.0.2:53 (rcode=0):
  - `ip-172-31-0-2.ec2.internal` → 172.31.0.2
  - `ip-172-31-0-3.ec2.internal` → 172.31.0.3
  - `ip-10-0-0-2.ec2.internal` → 10.0.0.2
  - PTR `2.0.31.172.in-addr.arpa` → `ip-172-31-0-2.ec2.internal` (AmazonProvidedDNS naming)

The reachable hosts are real EC2 instances inside the VPC.

### 3. Not a global network opening — the defect is specific to the custom policy mode

Control experiment in a sandbox created with the **default allow-all** mode: the same probes to 172.31.0.2/172.31.0.3/10.0.0.2 (including :5432) are **all refused (RC 113 / ECONNREFUSED)**; only UDP :53 is answered (DNS whitelist). So the missing egress filtering is specific to the `custom` network-policy mode.

### 4. API-version independent

The same bypass reproduces via the legacy API: `POST /v1/sandboxes` with `{projectId, networkPolicy: {mode:"custom", allowedDomains:["httpbin.org"]}}` → the sandbox reaches 172.31.0.2:5432 (RC 0).

### 5. Region independent (as in the original report)

sfo1 and iad1 both affected.

### Negative control: cloud metadata is NOT exposed

169.254.169.254 (IMDS), 169.254.170.2 (ECS credential proxy) and 169.254.169.253 (:53) are firewalled in custom mode as well — TCP connects succeed but any HTTP request is answered with RST. This shows the firewall does filter the 169.254.0.0/16 range specifically, while the VPC-internal range is left open.

### Impact update

The custom network-policy mode of Vercel Sandboxes fails to filter egress toward the VPC-internal range. Any customer with a sandbox project can reach the internal network; the exposed real service is a PostgreSQL fleet on 172.31.0.2/172.31.0.3/10.0.0.2:5432 (SSL-negotiation banner `S`), with the rest of the internal range blackhole-accepting (an attacker can probe any service the vendor later binds to that range). Cloud metadata is not exposed.

Reproduction sandbox IDs (for cross-check): sbx_YVgQIPc4MgB287DeP38MzMVqXuWK, sbx_RA2RlStz3b5AVCQ9VE9jxdADK2DQ (both deleted after testing; the same result reproduces on any fresh sandbox with the custom policy).

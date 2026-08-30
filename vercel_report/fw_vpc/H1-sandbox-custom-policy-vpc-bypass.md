# Vercel Sandbox custom 网络策略模式下 VPC 内网 172.31.0.0/16 防火墙绕过

title: Vercel Sandbox "custom" network policy bypasses egress isolation: entire AWS VPC 172.31.0.0/16 reachable from sandbox, while default allow-all cannot
Asset: https://vercel.com/docs/sandbox (Vercel Sandbox)
Severity: MEDIUM
Weakness: CWE-284 (Improper Access Control)
Vulnerability class: Networking and Firewall

## Submission details (必含要素)

- Vercel Team ID: team_GIy1SZ444lspqeNbh4r8uAUg
- Vercel Project ID: prj_iyw2xfjP3RKPT7n8b8c1tBIxxK5F
- Vercel Sandbox ID: sbx_bXiZHfWkprtWEqcK8lp05VPjM4zS (allowcmp，同沙箱策略切换对照) / sbx_hZ2QLI6yXmdaUUz139Ml8cXzncF3 (fwcustom5，扩展采样) / sbx_q5JMSKybnLoT5G8JcUv1AMMFv8I3 (denyall3，deny-all 对照)
- PoC zip: 见附件 fw_vpc_poc.zip（guest 复现脚本 fw_mini_guest.py + 全部 4 阶段/扩展采样原始输出）
- Severity rationale: 对齐 bounty 表 Medium tier「Firewall policy 违例但无 secret exfil（到达应被拒绝的目的地）」——custom 模式（文档承诺默认拒绝）实际放行整个 AWS VPC 内网 172.31.0.0/16 任意端口 TCP，而同账号同沙箱 allow-all（默认，最开放）模式下该网段不可达（EHOSTUNREACH），属未记录的网络策略违例；未做认证、未读取任何数据，无 exfil 演示，故不报 High
- 确认知悉 severity-inflation 罚则：已读，接受 Vercel triage 按最大可证明影响定级

## Summary:

Vercel Sandbox 的 `custom` 网络策略模式（官方文档声明 "User-defined policies deny traffic by default and let you allow specific destinations"）在放行 VPC DNS 时意外放行了**整个私有/保留地址空间**：10.0.0.0/8、172.16.0.0/12（含实测 172.31.0.0/16）、192.168.0.0/16、100.64.0.0/10（CGNAT）、169.254.0.0/16（link-local）任意 IP 任意端口 TCP 全部可达，而同一沙箱在默认 `allow-all` 与 `deny-all` 模式下这些网段全部 EHOSTUNREACH（errno 113）。

**三模式同沙箱对照（铁证）**：

| 策略模式 | 私有/保留网段 TCP（采样 10/8、172.16/12、192.168/16、100.64/10、169.254/16） | 172.31.0.3:5432 (PG SSLRequest) |
|---|---|---|
| allow-all（默认） | 全部 OSERR:113 不可达（cidr2 15/15 采样） | OSERR:113 不可达 |
| **custom（allowedDomains=["httpbin.org"]）** | **全域 OPEN（cidr1 15/15 采样）** | **OPEN，返回 b'S'（PG 握手响应）** |
| deny-all | 全部 OSERR:113 不可达（denyall3） | OSERR:113 不可达 |
| custom（再次切换/复现） | 全域 OPEN | OPEN，返回 b'S'（可复现） |

**放行面测绘**（custom 模式，cidr1 沙箱）：5 个保留网段 × 3 随机 IP × 随机端口 = 15/15 TCP connect 全部成功；各网段随机 IP 的 5432 端口全部返回 PG SSLRequest 响应 b'S'（含 10.107.229.181、100.124.43.21、192.168.112.196、169.254.82.21 等），53 端口全部 connect 成功。公网对照（8.8.8.8/1.1.1.1/54.172.31.170:443）在 custom 下明文 HTTP 被 RST（DPI 按 SNI 过滤）、allow-all 下明文直达（cloudflare/awselb 400 响应）。

**5432 响应归属**：任意私有 IP 的 5432 均返回 b'S'，且 TLS ClientHello 后 EOF、明文 StartupMessage 后 RST（fw_pg_fp/fw_pg_tls）——判定为防火墙对 PostgreSQL 协议的显式处理/代理响应（文档："Postgres 协议由防火墙显式处理握手"），而非网段内存在大量真实 PG 服务器。私有网段内未发现真实业务服务响应（HTTP 明文→RST、SSH/MySQL/Redis banner→NODATA）。

**核心结论**：custom 策略模式放行了全部私有/保留地址空间的任意端口 TCP（很可能是为实现 VPC DNS 放行而错误放宽到整个 RFC1918/保留地址面），使 sandbox 获得了超出默认 allow-all 模式的网络访问面，违反了 custom 模式"默认拒绝"的文档语义，构成 sandbox 防火墙绕过（in-scope：defeating the sandbox firewall to reach unauthorized destinations）。

**加剧因素（deniedCIDRs 缓解无效 — silent fail-open）**：operator 尝试用 `deniedCIDRs` 限制私有网段放行时发现该字段对私有/保留网段**完全无效**：API 接受配置（200）、readback 确认已保存（`{"deniedCIDRs": ["172.31.0.0/16", ...]}`）、无任何报错，但数据层流量依然放行。同一字段对公网 IP 正常生效（deny `3.234.68.0/24` 后 curl 该网段失败）。即：被泄露的私有网段访问面**无法通过任何公开文档所述的策略字段收窄**，唯一"有效"缓解是切换到 deny-all/allow-all 整体模式（文档推荐粒度方案无效）。

**归因对照（allowedCIDRs 字段功能正常，排除"全部策略字段失效"）**：同沙箱逐步验证——`custom` 空策略 → 全拦（文档承诺 "behaves as deny-all" ✓）；`allowedCIDRs:["8.8.8.0/24"]` → 白名单外 IP（1.1.1.1:53）TCP 层 errno 113 拒绝 ✓、白名单内 IP 可达 ✓；`allowedCIDRs` 与 `deniedCIDRs` 同网段冲突 → deny 优先 errno 113 ✓（文档 "Denied ranges take precedence" 对公网成立）。**决定性反转对照（已复跑确认，npol1 沙箱连续三阶段）**：`allowedCIDRs:["172.31.0.0/16"]`（按文档显式配置私有网段访问）→ 172.31.0.2:5432 **errno 113 不可达**（Hobby 无 Secure Compute，显式私有 CIDR 不生效）；同会话切回 `allowedDomains:["httpbin.org"]` → 172.31.0.2:5432 **PG b'S' 可达**（复现）；再切 `deniedCIDRs` 场景 → 仍可达。即：私有网段放行面不是任何显式配置的结果，而是域名 allow 路径的意外错误行为，且显式私有 CIDR 配置路径（文档推荐）完全失效。

## Steps To Reproduce:

1. 创建 Vercel Sandbox（Hobby 计划，任意 project），通过 API 设置网络策略为 custom：
   ```
   POST /v2/sandboxes/sessions/{sid}/network-policy
   {"mode": "custom", "allowedDomains": ["httpbin.org"]}
   ```
2. 在沙箱内执行（Python 最小复现，仅 TCP connect + 8 字节 PG SSLRequest，未认证未读数据）：
   ```python
   import socket, struct
   pg = struct.pack('!II', 8, 80877103)          # PG SSLRequest
   s = socket.socket(); s.settimeout(2.5)
   s.connect(('172.31.0.3', 5432))
   s.sendall(pg)
   print(s.recv(8))                              # -> b'S'  (PG 支持 SSL 握手响应)
   ```
   观察输出：`OPEN DATA=b'S'`
3. 将同一沙箱策略切回 allow-all（`{"mode": "allow-all"}`），重复步骤 2：
   观察输出：`OSERR:113`（EHOSTUNREACH，连接失败）
4. 再切回 custom，重复步骤 2：`OPEN DATA=b'S'`（可复现，见附件 4 阶段对照）
5. 扩展验证（custom 模式）：
   - 私有网段全量采样：10.0.0.0/8、172.16.0.0/12、192.168.0.0/16、100.64.0.0/10、169.254.0.0/16 × 随机 IP × 随机端口 → 15/15 TCP connect 全部成功（附件 cidr1）
   - allow-all 对照：同一脚本同一随机种子 → 15/15 全部 OSERR:113（附件 cidr2）
   - 172.31.0.0/24 全段 14 端口扫描：35 个 IP 的 5432 返回 b'S'（附件 fw_custom4b）
   - 25 个随机子网 × 5 IP = 125/125 采样全部返回 b'S'（附件 fw_vpc_deep）
   - 对照 deny-all：全部 OSERR:113（附件 denyall3）
6. **缓解尝试（deniedCIDRs 无效，npol1 沙箱，readback 逐步确认）**：
   a. `{"mode":"custom","allowedDomains":["httpbin.org"],"deniedCIDRs":["172.31.0.0/16"]}` → 200 保存成功，readback 确认；沙箱内 PG 探针 172.31.0.2:5432 → `b'S'`（与无 deny 基线一致，deny 未执行）
   b. `{"mode":"custom","allowedDomains":["httpbin.org"],"deniedCIDRs":["172.31.0.0/16","10.0.0.0/8","100.64.0.0/10","192.168.0.0/16","169.254.0.0/16"]}` → 200 保存成功，readback 全部确认；PG 探针 172.31.0.2 / 10.0.0.2 / 192.168.0.2:5432 → 全部 `b'S'`（deny 未执行）
   c. **字段本身工作正常对照**：同沙箱 `deniedCIDRs:["3.234.68.0/24"]`（公网 httpbin IP 网段）→ readback 确认；curl --resolve httpbin.org:443:3.234.68.252 → FAIL（连接失败，deny 对公网生效）
   d. 对照 deny-all 模式：PG 探针不可达（errno 113）——仅整体模式切换可阻断私有网段
7. **归因对照（allowedCIDRs 功能正常 + 显式私有 CIDR 反转）**：
   a. `{"mode":"custom"}`（空）→ curl httpbin.org FAIL（文档承诺 "A user-defined policy with no allowed domains or CIDR ranges behaves as deny-all" ✓）
   b. `{"mode":"custom","allowedCIDRs":["8.8.8.0/24"]}` → 8.8.8.8:53 TCP 可达；1.1.1.1:53 → errno 113（白名单外 TCP 层拒绝 ✓，IP 白名单字段工作正常）
   c. `{"mode":"custom","allowedCIDRs":["8.8.8.0/24"],"deniedCIDRs":["8.8.8.0/24"]}` → 8.8.8.8:53 → errno 113（公网场景 deny 优先于 allow ✓）
   d. **`{"mode":"custom","allowedCIDRs":["172.31.0.0/16"]}`（文档推荐的私有网段显式配置）→ 172.31.0.2:5432 → errno 113 不可达**——显式允许私有网段反而不可达，而仅 allow 公网域名时私有网段全域可达 → 私有网段放行面为域名 allow 路径的意外行为（非任何显式配置）
   e. **反转复跑确认**（同沙箱下一会话）：A: `allowedDomains:["httpbin.org"]` → PG b'S'；B: `allowedCIDRs:["172.31.0.0/16"]` → PG errno 113；C: 切回 `allowedDomains` → PG b'S'（复现）；D: deny-all → errno 113——三阶段对照稳定，排除时序/环境因素

## Supporting Material/References:

同沙箱策略切换 4 阶段（allowcmp，同一 sandbox 同一目标 IP 端口，仅策略不同）：

* P1 allow-all：T1 172.31.0.3:5432 -> OSERR:113；T4 httpbin.org:443 -> OPEN(awselb 400)
  `{"data":"[..] T1 172.31.0.3:5432 -> OSERR:113\n[..] T4 httpbin.org:443 -> OPEN DATA=b'HTTP/1.1 400 Bad Request\\r\\nServer: awselb'"}`
* P2 custom：T1 -> OPEN DATA=b'S'；T4 httpbin.org:443 -> RST（明文 HTTP 无 SNI 被 DPI 拒绝，符合文档 "Plain-text HTTP cannot be filtered by domain"）
  `{"data":"[..] T1 172.31.0.3:5432 -> OPEN DATA=b'S'\n[..]"}`
* P3 deny-all：全 OSERR:113（含 DNS 172.31.0.2:53）
  `{"data":"[..] T1 172.31.0.3:5432 -> OSERR:113\n[..] T2 172.31.0.2:53 -> OSERR:113\n[..]"}`
* P4 custom（again）：T1 -> OPEN DATA=b'S'（复现成功）
  `{"data":"[..] T1 172.31.0.3:5432 -> OPEN DATA=b'S'\n[..]"}`

扩展采样（custom 模式）：

* cidr1（新）私有网段测绘：10/8、172.16/12、192.168/16、100.64/10、169.254/16 × 随机 IP:随机端口 = 15/15 OPEN；各网段随机 IP:5432 全部 b'S'、:53 全部 OPEN
* cidr2（新）allow-all 对照：同脚本同种子 15/15 OSERR:113；公网明文 HTTP 直达（cloudflare/awselb 400）
* http_probe（新）custom 私有网段真实服务区分：明文 HTTP GET → RST（DPI）、SSH/MySQL/Redis banner → NODATA（黑洞，无真实服务响应）
* fw_custom4b：172.31.0.0/24 × 14 端口，35 IP 的 5432 返回 `DATA b'S'`（172.31.0.3/4/17/18/26/27/34/38/61/72/78/80/81/82/87/94/100/101/109/116/120/125/138/140/150/156/171/181/193/200/203/205/215/226/241）
* fw_vpc_deep：12 采样全部 `SSL_OK S`；sandbox 特征端口（23456/26661/30002/33090/34121）8 IP 全 RST（目标非其他租户 sandbox）；扩展采样 **125/125 PG_FOUND b'S'**（172.31.57/140/71/44/16/111/13/214/142/81/174/110/1/2/10/20/30/50/60/90/100/150/200/220/250 子网）
* fw_pg_fp：明文 StartupMessage -> RST 9/9（PG 要求 TLS 或 DPI 拦截）
* fw_pg_tls：TLS ClientHello -> EOF 9/9（无法完成 TLS 握手，未认证）

对照（不可达基线）：

* denyall3（deny-all）：172.31 全域 OSERR:113，0 开放端口，httpbin/8.8.8.8 全拦
* fw_custom3 allow-all：172.31.0.2 全端口 + 12 随机 IP 采样全 OSError
* fw_custom3 custom：172.31.0.2 全端口（22/80/443/3306/5432/6379/8080/9090/23456/26661/30001/30002/33090/34121/50000/60000）全部 OPEN；12 随机 IP 采样全 OPEN

官方文档对照（https://vercel.com/docs/sandbox/concepts/firewall）：

* "User-defined policies deny traffic by default and let you allow specific destinations"
* "Plain-text HTTP cannot be filtered by domain, and must be allowed by IP range instead"
* "A user-defined policy with no allowed domains or CIDR ranges behaves as deny-all"
* "Allowed address ranges: ... Use address ranges for non-encrypted traffic or **private network access through Secure Compute**"（私有网络访问需显式配置 CIDR + Secure Compute）
* "When a policy has allow rules, domain and address range rules apply independently. Domain rules do not narrow the IP addresses allowed by subnets.allow."

SDK Reference 示例对照（https://vercel.com/docs/sandbox/sdk-reference）：

* `updateNetworkPolicy({allow: ["google.com", ...]})` → 注释原文 "**Allow traffic to specific websites only**"（仅域名白名单）
* 访问私有网络需显式追加：`subnets: { allow: ["10.0.0.0/8"] }`（注释原文 "Allow traffic to specific websites **and private network**"）——**文档明确区分：仅域名白名单 ≠ 放行私有网段**

官方博客对照（https://vercel.com/blog/a-sandbox-without-a-network-boundary-is-only-half-a-sandbox）：

* "Reach a private service, **while blocking the rest of the private address space**"（官方宣称可只放行私有服务单点、**阻止其余全部私有地址空间**）
* "granular policies that **deny unmatched traffic by default**"
* "The firewall ... checks that hostname against the sandbox's domain policy **and also checks the destination address against its CIDR policy**"（每个连接都要过 CIDR 检查——实测 deniedCIDRs 对私有网段不执行，与该声明直接冲突）
* 仅域名 allow 的示例策略："**Other destinations are denied by default**"
* 安全边界基本属性（"fundamental properties of the execution environment"）："Which private address ranges are unavailable?"（哪些私有地址段不可达是 sandbox 的核心安全承诺）

Firewall 文档 denied ranges 对照（https://vercel.com/docs/sandbox/concepts/firewall）：

* "**Denied ranges take precedence over allowed domains and address ranges**"（deny 优先于 allow——实测对私有网段不成立，deny 与 allow 同时配置时私有网段仍放行）

Secure Compute 对照（https://vercel.com/docs/networking/secure-compute）：

* Secure Compute 为 **Enterprise-only** 功能（专用私有网络 + VPC peering，需显式创建并连接项目）；本次测试账号为 Hobby 计划，未配置任何 Secure Compute 网络，排除"私有网段放行来自 Secure Compute"的解释

**文档符合性结论**：本报告测试策略为仅 allowedDomains=["httpbin.org"]（无 subnets.allow），文档承诺仅放行该域名（"deny traffic by default" + "specific websites only"），实际放行全部私有/保留网段——**与官方文档三处声明直接冲突，非 documented behavior，不适用 Out of scope #4（文档未记录此行为，反而明确要求私有网段访问需显式 subnets.allow 配置）**。

## Impact:

- **防火墙策略语义被破坏**：用户选择 custom 模式（期望"默认拒绝，仅放行指定域名"）反而获得了比默认 allow-all 更大的网络访问面——全部私有/保留地址空间（10/8、172.16/12、192.168/16、100.64/10、169.254/16）任意 IP 任意端口 TCP 可达。custom 模式实际效果与文档承诺相反。
- **内网可达面扩大**：sandbox 可连接任意私有网段任意端口，可探测/连接各网段 5432（PG 协议代理响应 b'S'）与 53 端口；若这些网段内存在真实业务服务（AWS VPC 内资源、Vercel 生产网络、未来其他租户资源），将可直接触达。
- **IMDS/MMDS 面暴露**：169.254.169.254:80/443 在 custom 下 TCP 可达（allow-all 下 errno 113），当前无数据响应（Vercel 未启用 IMDS 内容），但 link-local 元数据面的隔离已被绕过。
- **潜在跨租户/生产资源风险**：若 10/8、172.16/12 等网段承载 Vercel 生产服务或其他租户资源（跨 VPC 互联、共享服务），sandbox 用户可触达（本次验证私有网段内未发现真实服务响应，但可达性本身已成立）。
- **数据外泄防护失效**：依赖 custom 策略限制 sandbox 出站的用户（如阻止访问内网/敏感网段）将无法获得承诺的保护。
- **缓解机制完全失效（silent fail-open）**：文档承诺 "Denied ranges take precedence over allowed domains and address ranges"，实测 `deniedCIDRs` 对私有/保留网段（172.31.0.0/16、10.0.0.0/8、192.168.0.0/16 等）不执行——API 返回 200、readback 正常、无任何错误提示，operator 无法通过该字段收窄暴露面；修复前用户唯一可用缓解是放弃 custom 模式整体切换 deny-all（丧失全部放行能力）。
- **审计/合规风险**：因策略"保存成功"且 readback 正常，依赖策略审计的租户（如合规要求记录 deniedCIDRs 配置）会误判防护已生效，实际处于无防护状态。
- **文档推荐配置方向完全失效**：按官方文档显式配置 `allowedCIDRs:["172.31.0.0/16"]`（"Use address ranges for ... private network access"）反而得到 errno 113（不可达），而未做任何私有网段配置的纯域名 allow 策略却意外获得全域私有网段可达——用户无法通过文档路径"得到"私有网段访问（Secure Compute 为 Enterprise-only），却可通过纯域名策略"意外获得"，配置语义与实际行为完全脱节。

合规说明：所有验证仅执行 TCP connect + 协议握手指纹（PG SSLRequest 8B / TLS ClientHello / 明文 HTTP GET / SSH/MySQL/Redis banner），未进行任何认证、未读取任何数据、未写入任何状态。影响评估基于可达性与握手响应。

建议修复：custom 模式下内网放行规则应从全部私有/保留地址空间收窄到仅 VPC DNS（如 172.31.0.2:53）或按 allowedDomains/CIDR 白名单精确匹配；并复核 allow-all 与 custom 模式可达性差异的根因（疑似 custom 模式插入的 DNS 放行路由意外覆盖整个 RFC1918/保留地址面）。

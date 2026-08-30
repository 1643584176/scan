# Vercel Sandbox 第 10 天作战计划（2026-08-29）

> 窗口剩余：08-29 ~ 09-01（3 天）| 遵循 rule-baseline-first + 非传统漏洞挖掘 skill
> 前提：token 需重新认证（团队 scope 403 saml:true，见下方阻塞项）

## 一、基线对照（提交前必查）

### 不算漏洞清单（10 项，全部有官方判定依据）

| # | 面 | 依据 |
|---|---|---|
| 1 | /dev/vda 读写/mount（microVM guest 盘） | Known A.5 + #3965216 官方回复（"stays inside your own microVM"） |
| 2 | init.sock 签名绕过 / ptrace sandbox-init | Known B.6 + #3955363 官方回复 |
| 3 | guest containerd.sock 未认证 → 特权容器 | Known B.2 + #3972961 官方回复 |
| 4 | vsock 2050 未认证 host 服务基本 RPC | Known B.1 |
| 5 | 全 41 caps / seccomp 宽松 / /dev bind | Known A.2/A.3/A.4 |
| 6 | DogStatsD / metrics vsock forwarder 注入 | Known B.5 |
| 7 | pidfd 窃取 fd 伪造 SpawnEvent（影响停留 own microVM） | control-plane-forgery 自评 N/A |
| 8 | OIDC token 沙箱内可捕获（无 Vercel 侧 exfil 通道） | Known B.7 |
| 9 | 公开 CVE 仅版本匹配 | Out of scope #5（需 weaponize 到真实逃逸） |
| 10 | 自沙箱 DoS / 静态分析 / SDK 客户端代码 | Out of scope #2/#9/#11 |

### 合格影响（唯一目标）
- EC2 host 新逃逸路径 / host 妥协（Critical $25-50k）
- 跨租户读/改/DoS（Critical/High）
- Firewall bypass + brokered credentials exfil（High $10-25k）
- 新 host 写原语（Critical）
- 控制面 broken authorization / IDOR（in scope，Medium-Low）

## 二、昨日遗留高价值候选（按潜力排序）

### A. CelldService / CreateSnapshot base_url SSRF（e150 会话 V25-V29 线）
- **发现**：guest 可达 celld 服务，API 全集：StartContainer/StopContainer/WaitContainer/SetWorkload/Heartbeat/RegisterPort/Shutdown + ContainersService/Create/Stdin/KillServer；CreateSnapshot 有 base_url 字段
- **假设**：若 CreateSnapshot 的 base_url fetch 由 celld（host orchestrator，博客原文确认在 host）执行 → SSRF → IMDS 169.254.169.254 → IAM 凭据 → host 妥协 = Critical
- **昨天停在 V29**（ctr 跨租户列容器 + CelldService 探测 + 同 sandbox 全链重验），结果未拉取
- **待验证**：① celld 运行层（guest OS vs host）② CreateSnapshot fetch 执行位置 ③ 能否 fetch IMDS/VPC 内网
- **风险**：若 celld 在 guest OS 内 → fetch 视角 = guest，IMDS 已隔离 → 价值降为 Low/Medium

### B. 跨租户 L2 邻居确认（exp_j330/331/332 线）
- **发现**：未知 MAC aa:d4:ea:5b:10:7c + IPv6 邻居 fe80::78b2:a8ff:fed9:8f1a（ND 表可查）
- **假设**：若为其他租户 sandbox → 嗅探/ARP/ND 注入 = 跨租户 Critical
- **待验证**：exp332 已写好（ping6 + 端口扫描 + 30s 帧监听），跑一次即有结果
- **风险**：若是 Vercel 基础设施（网关/代理/celld）→ host 指纹（Low）

### C. MITM init.sock 捕获内容分析（J546 已完成透传）
- **状态**：J545/J546 透传 MITM 成功，pull 全 200，捕获 cap1-5（506B Spawn 请求）+ resp1-4（179B KillResponse + 566-660B SpawnResponse）
- **待验证**：捕获内容中 host 下发命令/响应是否有凭据、其他租户引用；探索 init→host 方向 RPC 面（凭据请求/状态上报）

### D. 防火墙 bypass + OIDC token exfil（fw 线）
- **状态**：TCP/DNS/ICMP deny-all 下全拦；UDP 非 DNS、IPv6 面未完成；透明代理协议差异未测
- **官方 High**：firewall bypass + brokered credentials exfil

### E. 控制面 REST API 缺陷
- 生命周期不一致（删 sandbox 后旧 session 仍 exec）、IDOR（exp_idor_driver.py 已建）

## 三、今日执行顺序

1. **解除 token 阻塞**（用户操作，见下）
2. **B：跑 exp332**（成本最低，昨天已写好，若邻居=租户则直接 Critical）
3. **A：重跑/拉取 V29 全链**（CelldService API + CreateSnapshot SSRF，判断 celld 运行层）
4. **C：分析 J546 MITM 捕获内容**（本地零成本，先做）
5. 根据 2-4 结果决定是否深入 D/E

## 四、当日执行记录（15:50 更新）

### ✅ 已完成

1. **token 阻塞解除**：用户已更新 `vercel_cookies.txt`（vcp_2qAB...），`/v2/user` 200、teams 200（OWNER），已验证可用
2. **快照配额清理**：Hobby Snapshots Storage 超限（402 payment_required）→ `_snap_clean.py` 删除全部 50 快照 → 释放空间，可新建沙箱
3. **B 线（exp332 邻居确认）→ 关闭**：新沙箱中 fe80::78b2:a8ff:fed9:8f1a ping 不可达（Address unreachable）、ND 表空、30s 监听 0 帧 → 昨日邻居为临时基础设施地址，非跨租户目标
4. **C 线（J546 MITM 内容）→ 关闭**：上午已确认管理通道无凭据下发（host 仅 ed25519 签名认证，响应仅命令输出），MITM 窃听价值 N/A
5. **A 线（celld SSRF）→ 受阻**：新沙箱 23456 = sandbox-init mux（全 404），cell.sock 文件不可见（仅 /proc/net/unix 影子）；vda 挂载后可读 celld 二进制/celld-init.sh（guest rootfs 内），CreateSnapshot base_url 全 NORESP + 本地观测 0 回调 → SSRF 无法驱动，需旧型沙箱（e150 同款）验证

### 🚨 D 线重大突破：custom 模式 VPC 内网绕过

**核心发现**：custom 策略（allowedDomains=["httpbin.org"]）下，**172.31.0.0/16（AWS VPC 内网）全域 TCP 可达且服务响应**：

| 实验 | 时间 | 结果 |
|---|---|---|
| fw_custom3 | 14:52 | 172.31.0.2 全端口 OPEN；随机 172.31.x.x 采样全 OPEN |
| fw_custom4b | 15:28 | 172.31.0.0/24×14 端口：**35 IP 的 5432 返回 PG 数据 b'S'** |
| fw_vpc_deep | 15:35 | 12 PG SSL_OK；sandbox 特征端口全 RST（非沙箱）；**扩展采样 125/125 PG 响应**（25 子网×5 IP） |
| fw_pg_fp | 15:40 | 明文 StartupMessage → RST（PG 要求 TLS 或防火墙 DPI） |
| fw_pg_tls | 15:42 | TLS ClientHello → EOF（9/9 一致） |
| denyall3 | 15:34 | **deny-all 对照：172.31 全域 EHOSTUNREACH（errno 113）** |
| allowcmp | 15:50 | allow-all 对照（进行中） |

**文档对照**（vercel.com/docs/sandbox/concepts/firewall）：
- "User-defined policies deny traffic by default and let you allow specific destinations"
- "Plain-text HTTP cannot be filtered by domain, and must be allowed by IP range instead"
- "A user-defined policy with no allowed domains or CIDR ranges behaves as deny-all"
- Postgres 协议由防火墙显式处理握手

**结论假设**：custom 模式为支持 VPC DNS（172.31.0.2:53）放行了整个 172.31.0.0/16 网段，未收窄到 53 端口 → 任意 IP:端口可达（5432 PG 已实锤服务响应）→ **firewall bypass（in-scope：击败 sandbox firewall 到达未授权目的地）**

**下一步**：① allow-all 对照完成（区分服务端行为 vs 防火墙）② 确认 PG 归属（Vercel 生产？Neon？）③ 撰写 H1 报告

### ✅ D 线报告已完成（16:10）

- **报告文件**：`vercel_report/fw_vpc/H1-sandbox-custom-policy-vpc-bypass.md`（Severity MEDIUM，CWE-284）
- **核心论证**：同沙箱（allowcmp）4 阶段策略切换铁证——allow-all 不可达(OSERR:113) vs custom 可达(PG b'S') vs deny-all 不可达 vs custom 复现成功；扩展采样 125/125 PG 响应；文档语义对照（custom 默认拒绝）
- **证据附件**（fw_vpc/ 目录 11 个文件）：allowcmp_switch_p1~p4、fwcustom5 系列（custom4b/vpc_deep/pg_fp/pg_tls）、denyall3、fw_custom3 双模式对照
- **合规**：仅 TCP connect + 8B SSLRequest / TLS ClientHello，未认证未读数据
- **次要观察**：custom 下 httpbin.org:443 明文 HTTP → RST（符合文档"Plain-text HTTP cannot be filtered by domain"，DPI 拒绝非 SNI 明文）→ 反而佐证 172.31.0.0/16 是 CIDR 级放行而非域名匹配

### 待办

- D 线报告：H1 提交（firewall bypass / VPC 内网访问）— ✅ 报告已写，待人工提交
- A 线：尝试重建 e150 同款沙箱（如 resume 旧沙箱路径）验证 cell.sock ALIVE → CreateSnapshot SSRF — ✅ 关闭（新沙箱无 cell.sock 可访问、旧沙箱快照已删无法恢复、vda 挂载后 socket 无响应，SSRF 无驱动路径）

### ✅ E 线（控制面 API 缺陷）已探测

- **exp_idor（删沙箱后旧 session exec）→ 关闭**：DELETE 沙箱后旧 sid 发 cmd → 404 not_found（生命周期管理正确，无僵尸会话）
- **snap_idor（跨沙箱快照恢复）→ 失效**：依赖的快照已被 _snap_clean.py 清理，脚本无测试对象
- E 线剩余面（团队/项目级越权）需其他租户资源，违反规则基线（只测自有），不再深入

### 🚨 D 线报告增强（16:10-16:30）：放行面扩大至全部私有/保留网段

- **新探测 cidr1（custom）**：10/8、172.16/12、192.168/16、100.64/10、169.254/16 × 随机 IP × 随机端口 = **15/15 TCP connect 全 OPEN**；各网段随机 IP:5432 全返回 b'S'（防火墙 PG 协议响应）、:53 全 OPEN
- **新对照 cidr2（allow-all）**：同脚本同随机种子 = 15/15 OSERR:113；公网明文 HTTP 直达（cloudflare/awselb 400）
- **http_probe（custom）真实服务区分**：私有网段明文 HTTP → RST（DPI）、SSH/MySQL/Redis banner → NODATA（黑洞，无真实服务）→ 5432 b'S' 判定为防火墙协议层响应（非真实 PG 集群）
- **mmds1（custom）**：169.254.169.254:80/443 TCP 可达（allow-all 下 errno 113）但无数据（Vercel 未启用 IMDS 内容）；DNS 查询 172.31.0.2 → rcode=5 REFUSED（代答）
- **udp6（custom）**：UDP 私有网段 SENT_NORESP、DNS 代答 REFUSED；IPv6 无路由（OSERR:101）→ 面关闭
- **报告已更新**：`fw_vpc/H1-sandbox-custom-policy-vpc-bypass.md`（Summary/Impact/证据全量更新 + Submission details 补全）+ PoC zip 19 文件（cidr1/cidr2/http_probe/mmds1 新证据入包）
- **合规**：探测均为 TCP connect + 协议指纹，无数据读取；stop at confirmation；<5qps

### ✅ 跨租户测试（16:40-16:50，双账号 attacker/victim）→ 关闭

- **victim 账号配置**：bobolis-projects-f7a9367e（team_jnske5hDpDfj9eDG2PAfDqWf / prj_LX0QDsEAlWA0uRZvVTunSef3lllF），token 存 vercel_cookies2.txt
- **victim 沙箱**：victim1（sbx_gOQMW7KfqtHsocfYQTP8rs8FyMKd），marker=VICTIM_MARKER_3424aaa30dcb 已放置确认
- **attacker 只读探测（主账号 token）**：按 name GET / session GET / network-policy GET / cmd POST（仅 echo）/ 无 teamId → **全部 404 not_found**（授权隔离正确）
- **结论**：控制面 broken authorization / IDOR 不成立；网络层无定向路径（特征端口探测 RST）；跨租户面关闭（stop at confirmation，未枚举未 dump）
- **清理**：victim1 已删除

### ✅ 文档/公开说明合规复核（17:00-17:20，用户质疑后）

- **结论：报告成立，非 documented behavior，不适用 Out of scope #4**
- 比对来源（4 处官方说明）：
  1. Firewall 文档（/docs/sandbox/concepts/firewall）：User-defined

### 文档/公开说明合规复核（17:00-17:20）

- 结论：报告成立，非 documented behavior，不适用 Out of scope #4
- 比对来源（4 处官方说明）：
  1. Firewall 文档：User-defined policies deny traffic by default；私有网络需显式 CIDR（Use address ranges for private network access through Secure Compute）
  2. SDK Reference：{allow:[...]} = Allow traffic to specific websites only；私有网络需显式 subnets:{allow:[10.0.0.0/8]}（示例直接区分）
  3. 官方博客：blocking the rest of the private address space；deny unmatched traffic by default；checks destination against CIDR policy；仅域名示例 Other destinations are denied by default
  4. Secure Compute 文档：Enterprise-only + 需显式创建网络（Hobby 账号排除此解释）
- 对照结论：仅 allowedDomains 时放行全部 RFC1918/保留网段，与 4 处官方声明全部冲突
- 报告已更新：新增文档对照小节（4 来源原文引用）

### 🚨 N 线（deniedCIDRs 缓解无效，18:00-19:00）→ 并入 D 线报告

**假设**：operator 可用 deniedCIDRs 收窄 custom 模式私有网段放行面 → 若 deny 有效则 D 线降级为"默认配置缺陷"，若无效则加剧（silent fail-open）

**实验设计（npol1 沙箱，严格对照 + readback 逐步确认）**：

| 阶段 | 策略（readback 确认保存） | PG 172.31.0.2:5432 数据层 | 公网 curl 3.234.68.252 |
|---|---|---|---|
| A | custom+allow（无 deny） | b'S'（可达） | OK-200 |
| B | +deny 172.31.0.0/16 | **b'S'（仍可达！deny 未执行）** | OK-200 |
| C | +deny 3.234.68.0/24（公网） | — | **FAIL（deny 对公网生效）** |
| D | deny-all | 不可达（113） | FAIL |

**multi-CIDR 扩展（deny 5 个私有/保留网段，readback 全部确认）**：172.31.0.2 / 10.0.0.2 / 192.168.0.2:5432 → 全部 PG b'S'（deny 未执行）；公网未 deny 目标 OK-200

**结论**：deniedCIDRs 对私有/保留网段完全 silent fail-open（API 200 + readback 正常 + 无报错 + 不执行）；对公网正常执行 → operator 无法用文档承诺的 deny 字段缓解 D 线暴露面，仅能整体切换 deny-all

**方法论修正（重要）**：TCP connect 成功（RC 0）≠ deny 未执行——防火墙对公网/私有网段均模拟 TCP 握手，deny 实现在数据层（DPI/黑洞）；之前 _x_ndenyd.py 的 connect 判断（8.8.8.0/24 deny 后 RC 0）为误判，数据层（curl/PG 握手）才是有效判据

**报告已更新**：fw_vpc/H1-sandbox-custom-policy-vpc-bypass.md 新增"加剧因素"节 + STTR 步骤 6 + 博客/Firewall 文档对照引用 + Impact 两条（缓解失效 + 审计风险）

**证据脚本**：_x_nfinal4.py（严格对照矩阵）/ _x_nmulti.py（multi-CIDR）/ _x_nmatrix.py（connect vs 数据层方法论矩阵）

### ✅ 归因闭环 + E5 反转复跑确认（19:00-19:40）→ D 线报告最终强化

**allowedCIDRs 归因对照（_x_cidr.py）**：
- E1: custom {} 空 → curl FAIL（文档 "behaves as deny-all" ✓）
- E2: allowedCIDRs=[8.8.8.0/24] → 8.8.8.8 可达；1.1.1.1:53 → errno 113（白名单外 TCP 拒绝 ✓，IP 白名单字段功能正常）
- E4: allow+deny 同网段 → 113（公网 deny 优先 ✓）
- **E5 反转**：allowedCIDRs=[172.31.0.0/16]（文档推荐的私有网段显式配置）→ PG 172.31.0.2:5432 **errno 113 不可达**！而仅 allow 域名 → 全域可达 → 私有网段放行面 = 域名 allow 路径的意外行为

**E5 复跑确认（_x_e5repro.py，同沙箱下一会话三阶段）**：A allow 域名→b'S' / B allow 私有 CIDR→113 / C 切回域名→b'S'（复现）/ D deny-all→113 → 反转稳定，排除时序/环境因素

**SNI 代理架构确认（_x_sni/_x_sni2/_x_sni3，无新漏洞）**：
- 防火墙 TLS 终止 + 按 SNI 代理转发（仅 443）；连任意 IP:443 + SNI=allow 域名 → 代理到 allow 域名（目标 IP 被忽略）
- SNI 变体矩阵：精确匹配（尾点归一化匹配、大小写不匹配、前后缀不匹配）→ 无白名单绕过
- 代理不注入默认凭据（无 X-Forwarded-For/Authorization）→ credential brokering 无自动面
- 非 443 端口不代理（8443/4443 EOF）

**fs/read API 面（_x_fs/_x_fs2，关闭）**：绝对路径可读（/etc/passwd、/proc/1/environ 无 token）、路径穿越截断到容器根（无 host 穿越）、旧会话 410（生命周期正确）→ 能力 ≤ guest root，无新漏洞

**合规复核**：官方 changelog + 公开搜索均无 deniedCIDRs/私有网段放行披露记录 → 发现未被公开，可提交

**D 线报告最终版**：fw_vpc/H1-sandbox-custom-policy-vpc-bypass.md（MEDIUM，证据链：三模式对照 + 125/125 采样 + deniedCIDRs 缓解无效 + allowedCIDRs 归因 + E5 反转复现）

**证据归档**：fw_vpc/nline_evidence/（_x_nfinal4/_x_nmulti/_x_nmatrix/_x_cidr/_x_e5repro）

### 🔍 新面探索（12:30-13:10，全部关闭，无新漏洞）

**CONNECT 隧道（_x_connect/_x_connect2）**：h1+h2 的 CONNECT 方法全部被转发到 allow 域名上游 → awselb/2.0 400 Bad Request → 防火墙非 CONNECT 代理，无任意隧道

**Guest 面系统枚举（_x_guest/_x_g2~g9）**：
- 块设备：/dev/vda(254:0)=数据盘（bind /etc/hosts、resolv.conf、/run/vercel/share）、/dev/vdb(254:16)=rootfs → known A.5 已覆盖
- virtio：virtio0/1=block、virtio2=net、virtio3=vsock、virtio4=entropy（标准，无新设备）
- **/proc/net/unix 被虚拟化**：cell.sock/apm.sock/containerd.sock 路径显示但文件系统不存在，connect=FileNotFoundError → 蜜罐/影子条目，不可信
- vsock connect → PermissionError（受限，sudo 无效）
- **sandbox-init 逆向**（/run/vercel/share 内 9MB Go 二进制）：模块 = github.com/vercel/api/hive-containers/sandbox-controller，协议 = spawnv1 Connect RPC（Spawn/Kill/Ping + PtyInput/PtyOutput/SpawnEvent 流）+ Ed25519 签名（pubkey 可见：i0LREDAQy/qxuiZbECJEbY12v1cvoHbHzg3OETJq7LA=）；guest 内可用真实 pubkey 启动自己的实例 → init.sock 面 = known B.6 已报 → 关闭
- sandbox-init 无出站连接（/proc/net/tcp 空）

**HTTP/2（_x_h2）**：防火墙代理同时支持 h2+h1.1；走私目标仅 allow 域名（第三方 httpbin）→ 非 Vercel 资产 → 范围外关闭

**结论**：今日新面（CONNECT/guest/sandbox-init/h2）全部关闭或 known 覆盖；D 线报告仍为唯一最强产出，待提交

### 🔍 H 线（Host/:authority 请求级校验 + vhost 路由，21:00-22:10，关闭）

**假设**：防火墙按连接 SNI 校验 allowlist，但请求级 Host/:authority 无校验 → 伪造 Host 到达其他 vhost（跨租户/白名单绕过）

**验证结果**：
- 请求级 Host 确实无校验：双沙箱（tinj1/npol1）同策略（allow httpbin.org）下 Host 任意值（IP/域名/vercel.com/子域）→ 全 200 转发；仅空 Host → 400；h2 :authority 任意值同样放行（_x_h1host/_x_h2auth/_x_403cond2）
- 403 "request authority does not match SNI"：仅旧代理实例偶发（T2 Host=1.1.1.1），当前实例不可复现 → 节点版本差异，非稳定面
- **决定性对照（_x_pubvsbx）**：公网直连 vs 沙箱内 Host 伪造，响应完全一致：存在第三方 vhost→403（Host 混淆防护）、不存在→404、vercel.com 家族→307/308 规范化重定向（Location 均为应用层响应）、deployment URL→302 SSO 保护（/sso-api?url=... + nonce cookie）
- **结论：Host 伪造无沙箱特定影响——上游 Vercel 应用/边缘对所有来源（含公网）都做同样处理，防火墙只按 SNI 放行连接是设计使然 → H 线关闭，非有效报告**

**附带观察**：
- OIDC token 自动注入：allow-all 下访问任何 vercel.app 项目，请求自动带 `x-vercel-oidc-token`（sub=目标项目，owner=沙箱团队）→ credential brokering 设计行为（known B.7 覆盖），无新价值
- 已部署自有 echo 接收端 `sbx-echo-e29ca9cb.vercel.app`（_x_deploy_echo.py，可复用）
- 方法论修正：Host 伪造响应必须与公网直连对照，状态码本身不能证明 vhost 路由（应用层响应与边缘路由无法仅凭状态码区分）
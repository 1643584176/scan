# Vercel Sandbox HackerOne 完整政策归档(2026-08-28 用户提供)

> 来源: https://hackerone.com/vercel_sandbox(登录后页面全文)
> 归档日期: 2026-08-28 | 状态: 窗口 2026-08-18 ~ 09-01 UTC(23:59),池耗尽提前结束
> 本文件为政策原文整理;Known findings 小节为提交前自查核心依据

## Introduction / 项目概要

- 时间盒公共赏金,聚焦 Sandbox 隔离边界:Firecracker microVM、host 侧 sandbox firewall、credential brokering、sandbox control plane API
- 非 Vercel 平台赏金/开源项目:vercel.com、v0、dashboard、通用平台 bug 均不在内
- 联系: sandbox-escapes@vercel.com

## Rewards / 赏金总表

- Bounties per report, scoped 到单一 root cause;severity 由 Vercel triage 按**最大可证明影响**定,非自评、非 CVSS 单独
- 虚报 severity(无详细 rationale 对齐 bounty 表)→ 减 25%
- $50k 上限 = 跨租户读/改;部分影响按部分 tier 支付;同一 root cause 多份报告只付第一份完整可复现的

| Severity | Bounty | Typical impact |
|---|---|---|
| Critical | $25k–50k | MicroVM→EC2 host 逃逸,或跨租户读/改/RCE |
| High | $10k–25k | Firewall bypass + credential/data exfil,或跨租户 DoS |
| Medium | $5k–10k | Policy 违例但无 secret exfil 演示 |
| Low | $1k–5k | Hardening gaps, oracles |

- **AI slop / out of scope 提交 → N/A 或 Spam,零赏金**(AI 生成未人工验证、幻觉/未验证主张、无 working exploit 的扫描器输出)

## Overview(关键时间线)

- 窗口: 2026-08-18(周二) ~ 2026-09-01(周二)23:59 UTC;结束后提交不合格
- Triage: 开赛日至 2026-10-01(闭赛后一个月)
- 池: $1M;单报告上限 $50k

## Architecture(边界模型)

- 裸金属 EC2 host,单 host 多沙箱并发,每沙箱一个 Firecracker microVM(专用 guest kernel)
- host 侧 orchestrator 管理 microVM 生命周期;orchestrator 经 **jailer** 启动 Firecracker(chroot 受限目录树 + 专用 cgroup + namespace 隔离,即使 guest→host bug 也被 confine)
- microVM 内 init 经 runc/containerd 启动 Linux 容器运行用户代码
- **"Linux namespaces exist for developer experience, not for security; the Firecracker microVM is the actual security boundary"**
- 用户代码离 EC2 host 两层:Linux 容器 → Firecracker microVM

## In Scope(合格范围)

**真实沙箱逃逸**(满足任一):
1. 从 Firecracker microVM 逃逸到 EC2 host OS(实际信任边界)
2. 读/改其他租户数据(不属于你的沙箱的文件、环境、secrets、内存、网络流量)
3. 在 EC2 host 或其他租户沙箱执行代码
4. 崩溃/动摇同一 host 上其他租户沙箱(跨租户 DoS)

**Sandbox firewall bypass**(不达 host 也算):
- 击败 sandbox 网络防火墙(deny-all、domain allowlists、subnets.allow/deny、CIDR-only)到达未授权目的地
- 检索 credential brokering 凭据(注入的 OIDC token、转发 auth headers),且**不依赖**第三方网站反射

**Sandbox control plane 在内**:
- sandbox CLI / @vercel/sandbox 调用的 Vercel REST API:broken authorization / IDOR 读写他人沙箱、会话、网络/凭据配置;认证/访问控制绕过;其他控制面缺陷
- "You do not need to enumerate the endpoints: if the sandbox client consumes it, it is in scope"

## Out of scope(明确不收)

1. Linux 容器 namespace 逃逸仅到 Firecracker guest OS(PID/mount/net/disk/device namespaces)——多种已知方式,namespaces 是开发体验功能非安全边界
2. 自沙箱 DoS(崩溃/挂起/耗尽自己沙箱资源)——trivially reproducible,不奖励
3. 第三方网站反射 credential-brokering headers(仅 Vercel 侧缺陷泄漏才算)
4. 文档指示 operator 另行配置的行为(文档已记录的局限,如 domain allowlist 叠加 subnets.allow、CIDR-only 限制 DNS——文档警告过)
5. 公开 Firecracker/其他组件 CVE 仅版本匹配——**weaponize 到真实逃逸才算**:"a public upstream Firecracker vulnerability that you drive to a real escape to the EC2 host or to another tenant on a live Vercel Sandbox is eligible"
6. 需要 operator 无法提供的自定义内核/VMM 的攻击(guest kernel 固化在 EC2 实例)
7. Build-phase Dockerfile/Containerfile 构建环境问题(build context/cache/registry auth at build time)
8. Vercel Container Registry(VCR)问题(registry auth、blob push、OIDC vercel scope、VCR control plane)
9. 静态分析-only(必须 live PoC)
10. 非 Vercel 运营的服务漏洞(Datadog、AWS 等;报 Vercel 侧可达性)
11. @vercel/sandbox SDK 和 runtime 客户端代码(服务端 control plane 在内)
12. 其他非 Sandbox 的 Vercel REST API(account/team/project/deployment/dashboard/billing)

## Known findings(提交前必查,重复 root cause → duplicate 不付)

> "Reports that duplicate these root causes will be closed as duplicate and are not eligible for bounty, **unless the report demonstrates a materially new impact** (a new escape path to the EC2 host, cross-tenant reach, or a previously-unknown host write primitive). The primitive itself is a duplicate; any new impact is paid at the new impact's tier."

### A. Container → Firecracker guest OS namespace escape(已知,容器不是边界)

1. Writable /proc/sys/kernel/core_pattern + 共享 /volumes/opt/vercel bind mount → microVM initial PID/mount namespace 内 uid 0
2. **全部 41 个 Linux capabilities 授予沙箱容器**
3. Host /dev bind-mounted 进沙箱
4. Seccomp profile DefaultAction: ActAllow + 可绕过的 AF_VSOCK 规则
5. **mknod + mount microVM 系统盘(/dev/vda)**
6. 单 syscall 逃逸:可写 /proc/sys/kernel/modprobe + /sys/kernel/uevent_helper + /opt/vercel 读写 bind mount

### B. Post-escape host-side surface(已知,无新 host-compromise 原语不奖励)

1. vsock 2050 未认证 host 服务:resource-usage / proxy-CA / cache-oracle / OCI-image-config 读写 RPC
2. 逃逸后 outer-namespace 深度:containerd.sock、ipc.sock、APM/metrics sockets 世界可访问
3. 经 host control socket spawn 兄弟容器(仍 Firecracker-bounded,非 EC2)
4. CAP_SYS_ADMIN + 无限制 /proc/sys 写(kernel sysctl 面、dmesg/kptr 泄漏)
5. DogStatsD / metrics vsock forwarder 注入(无跨租户影响)
6. **sandbox-init Ed25519 key extraction**
7. (Credential brokering 类)x-vercel-oidc-token / x-vercel-protection-bypass / x-vercel-proxy-signature 注入未剥离;仅 Vercel 侧缺陷的 exfil 通道在内

> 链已知原语 → 新 host-compromise / 跨租户 / firewall-bypass-with-exfil → 按新影响 tier 付费

## Bounty table: Severity Guidelines(各 tier 示例)

### Critical($25k–50k)
- Firecracker microVM 逃逸到 EC2 host(VMM/jailer/snapshot-restore/virtio 0-day → host 代码执行)
- 跨租户读/改另一租户沙箱数据(无对方配合)
- 跨租户 RCE(他人沙箱或 EC2 host 上跑代码)
- 经 Vercel 侧配置错误/host 服务漏洞从 microVM 逃逸到 EC2 host(如 host-service vsock RPC abuse 升级为 host 妥协)

### High($10k–25k)
- Firewall bypass exfil credential brokering 凭据(OIDC tokens/转发 auth headers)到攻击者控制目的地
- 网络防火墙规避击败 deny-all/domain allowlists/subnets.deny,exfil operator 数据到未授权目的地
- 跨租户 DoS(崩溃/挂起/动摇同 host 其他租户)
- 影响同 host 其他租户的 VM 级崩溃/不稳定
- MMDS secret 披露(deny-all/CIDR deny 下读取 MMDS 内容:Datadog、凭据等)

### Medium($5k–10k)
- Firewall policy 违例但无 secret exfil(到达应被拒绝的目的地)
- Credential-brokering header 暴露到不明显反射的目的地(Vercel 侧缺陷)
- 逃逸后未认证只读 host-service RPC 滥用:host billing 数据/proxy CA 证书/跨沙箱 cache oracle
- Sandbox 网络策略持久化 bug(策略更新未持久化、resume 后失效、stale readback)
- ForwardURL / transform rule 绕过,将认证流量错误路由到攻击者影响的 origin

### Low($1k–5k)
- 已配置策略与实际执行行为的差距(live PoC、非文档解释、官方会改的)
- 正确但不重要的发现 → Informative 零赏金
- 沙箱 block 超过 operator 配置 = 产品 bug 非安全问题
- Silent fail-open(API 接受但未执行、无报错无 readback)
- Policy 规范化不匹配(case/IDN/trailing dot/wildcard depth/port suffix/unmasked CIDR/allow-deny 优先级;同解析 root cause = 一报告)
- Policy 生命周期缺口(resume/snapshot/restore 不重新应用、stale readback、boot 时未加载窗口)
- Brokered-credential hygiene(自己沙箱内不该出现处可读:logs/进程 args/env/磁盘 temp;scope/audience/lifetime 过宽)
- 跨租户 near-miss(同 host 上他租户存在/时序/活动的证据,无内容可恢复)
- Identifier 可预测性(熵显著不足且无可用性演示)
- Quota/metering 规避(无跨租户/host 影响)
- Host 实现披露(host build/config/topology 显著收窄攻击路径,无 secrets;无 reachability 的指纹 = Informative)

## Not eligible(closed Informative)

日志/审计缺失(执行本身有效)、内部端点版本 banner、缺失安全头、verbose 错误、capability/config 清单无可达性、文档与最佳实践建议、raw scanner output

## Rules of engagement

- 一报告一漏洞(除非链式演示影响)
- 重复:同一 root cause 只奖第一份完整可复现;已知原语新影响按新 tier
- **内部查重**:不仅对公开 Known findings,还对内部 tracker 查重(含未修复/未公开项,会给出记录日期和理由)
- Root cause 合并:同一底层问题多漏洞 = 一赏金
- 必须:详细复现步骤 + PoC zip(无法复现 → 不合格)
- 只测自己账户/有书面许可的账户;不要访问超过证明所需的数据;发现他人 personal data/secrets 立即停止、不下载、报告内脱敏
- 不装持久后门、PoC 后不留后门、不修改 host/tenant 状态超出证明所需
- 无社工、不威胁工作人员;Vercel 端点扫描限 **5 qps**,无 volumetric DoS
- AI 生成报告必须亲自验证 working PoC 和真实影响

## Testing guidelines(要点)

- 用自己的 H1 别名账号(vercel.com 注册,username@wearehackerone.com);Hobby 免费够用
- 跨租户测试:两个自己账号(attacker/victim);**stop at confirmation**——确认即停,不枚举/不 dump/不持久,第三方数据脱敏后上报
- 配置测试面:firewall(默认+hardened 两模式)、credential brokering、resources/lifecycle(跨租户副作用)、host services
- 复现:fresh sandbox 从 create 开始确认;记录命令/config/image/sandbox ID/team ID/project ID/timestamps

## Submission guidelines(必含要素)

1. PoC zip(必须;no PoC, no bounty;初版提交或按请求及时提供)
2. Vercel Team ID(team_…)
3. Vercel Project ID(prj_…)
4. Vercel Sandbox ID(sbx_…)
5. Vulnerability class:Cross-Tenant data access / Networking and Firewall / Denial of Service / Other
6. Severity + rationale(对齐 bounty 表)
7. 确认知悉 severity-inflation 罚则
- 纯理论/仅源码分析/"can provide PoC if needed" 不合格
- 补丁建议欢迎,可能影响在 range 内定级

## Disclosure policy(公开披露限制,重要)

- **Limited Coordinated Vulnerability Disclosure**;报告默认 private;未获 Vercel 书面批准不得公开细节(平台内披露需明确同意,沉默≠同意;resolved 不会自动披露)
- **Embargo**:报告关闭(任意状态)+ **2026-12-01 之后**(闭赛后 90 天);Critical/High 未修补时 Vercel 可书面延长一次至多 90 天(不晚于 2027-03-01)
- 禁令期外可说的:参加挑战、提交过报告、获得赏金(可报金额)、链接公开页面
- 禁令期前不得:复现步骤/PoC/exploit 细节、截图/视频/日志/内存 dump、内部 host 服务/vsock 端点/MMDS 内容/brokered 凭据/token/cookie/客户数据、非自己的 ID、可复现所需的技术细节(含博客/社交/会议/GitHub/Discord/pastebin/非合作者私享)
- Embargo 后:平台内披露默认 Limited(summary+timeline,PoC 附件隐藏);外部披露(blog/talk)提前 7 天给 Vercel 审稿;Vercel 可能赛后自行发布技术文
- **Never disclose**:客户/非己租户数据、生产凭据、brokered tokens、私钥、stop-at-confirmation 触及的数据
- 违规后果:报告失去赏金资格(含未付)、退出 Safe Harbor、可能按 Code of Conduct 处理
- 与本政策冲突时,本政策优先于 HackerOne 默认披露规则

## Safe Harbor

- 按政策善意的安全研究受 CFAA/DMCA 等反黑客法保护;不追诉
- 不覆盖:测试 out-of-scope 资产、超单次确认保留他租户数据、volumetric DoS、社工、披露 embargo 期细节

## Response targets

- 首次响应:1 business day;triage:5 business days;bounty 决策(自 triage):10 business days
- 合格报告 triage:开赛至闭赛后一个月(2026-10-01)

## Ineligible participants

现任/前任 Vercel 员工与承包商、员工直系亲属、发现/修复相关方(含付费渗透)、本项目 H1 员工

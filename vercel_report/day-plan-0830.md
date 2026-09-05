# Vercel Sandbox 第 11 天作战记录（2026-08-30，窗口 09-01 结束）

> 会话压缩存档（每 15 分钟更新）| 遵循 rule-baseline-first + 非传统漏洞挖掘 skill

## 当前唯一目标（官方 4 次重申的合格标准）
- EC2 host 新逃逸路径 / host 妥协（Critical $25-50k）
- 跨租户读/改/DoS（Critical/High）
- Firewall bypass + brokered credentials exfil（High $10-25k）
- 新 host 写原语（Critical）
- 控制面 broken authorization / IDOR（Medium-Low）

## 已提交报告状态（全部不可复用）
| # | 报告 | 状态 |
|---|---|---|
| 1 | H1-3954985 vda host disk | 自撤回（COW 快照非 host 盘） |
| 2 | H1-3955363 init.sock 签名绕过 | N/A（own microVM） |
| 3 | H1-3965216 mount vda | N/A（guest 盘，Known A.5） |
| 4 | H1-3972961 containerd.sock→特权容器 | N/A 19h 前（Known B.2，无新影响） |
| 5 | custom VPC bypass (fw_vpc) | dup of #3951926（domain-allow 缺 dest-IP 校验） |
| 6 | pidfd 控制面伪造 | 自评 N/A 未提交 |

## 今日会话进展（v40→v44）
1. **v40/v41/v42 Exec 线 → 死路**：Vercel 改版 ExecProcessRequest 字段布局确认（f1=container_id, f7=exec_id 有格式校验, f3=string 严格 UTF-8 验证）；任何有效 Exec → shim 崩溃 → task 目录残留无法重建 → 多次探测导致 sandbox 崩溃（410）。**关闭**
2. **v43/v43c RCE 链证据（= H1-3972961 重复，不提交）**：
   - 链：mknod /dev/vda → mount (xfs) → /mnt/vdax/run/containerd/containerd.sock → Containers/Create + Tasks/Create/Start（gRPC h2c 手工 protobuf）→ 特权容器
   - v43c 证据：marker `v43-pwned Sun Aug 30 07:25:45 UTC 2026`（宿主盘写）、CapEff=000001ffffffffff（全 caps）、Seccomp=0、netns 4026531833（guest init netns，非 host）、/mnt = guest 盘根目录
   - 官方判定：/dev/vda = microVM guest 盘；containerd.sock 世界可访问 = Known B.2 → 全部 N/A
3. **v44 UDP 三模式对照 → 面关闭（无 bypass）**：
   - 结果：deny-all 公网/私网 UDP 全 SENT_NORESP（拦截）；allow-all DNS RESP 61B（真实响应，默认宽松模式无意义）；custom 公网 UDP 全拦、私网 DNS 代答 rcode=5 REFUSED
   - 结论：UDP 非 DNS 出网被拦截，无独立 firewall bypass 根因；OIDC UDP exfil 无通道
4. **v44s 快照 IDOR → 隔离正确（关闭）**：发现自动快照机制（keepLastSnapshots count=1，642MB guest 盘快照，7 天过期）；victim 账号访问 attacker 快照 id → 404 "Snapshot not found."（资源级授权）；恢复端点全部 404（路径不存在）
5. **v44t 跨沙箱共享写 → COW 隔离（关闭）**：A 写 /run/vercel/share/.mark_xxx + /run/cell → B 读 No such file；mountinfo 均 bind 自各自 xfs /dev/root（per-sandbox COW）
6. **v44p 策略持久化 → 正常（关闭）**：带 custom 创建→PG b'S' 基线；stop（自动快照 snap_xxx）→ resume（新 session）后 sandbox+session.networkPolicy 均保持 custom（策略随 sandbox 重新应用）；生命周期端点：POST /v2/sandboxes/sessions/{sid}/stop = 200（新发现），其余 stop/pause/restart 均 404
7. **v44x 跨租户写操作 → 全部隔离（关闭）**：victim 改 attacker network-policy→404；DELETE attacker 快照→404（快照仍存在）；resume attacker sandbox→404；用 attacker projectId 列快照→404
8. **v44e 端点枚举 → 无新端点（关闭）**：21 个候选 GET 端点除已知 2 个（/v2/sandboxes/{name}、/v2/sandboxes/sessions/{sid}）外全部 404
9. **其他已关闭面**（昨天 day-plan-0829 记录）：celld SSRF（无驱动路径）、跨租户 L2（基础设施地址）、控制面 IDOR（404 正确）、Host 伪造（与公网一致）、CONNECT/h2/fs API（无新漏洞）、UDP 私网（SENT_NORESP，仅 custom 模式）
10. **v45-v50 forwardURL/transform 线 → 面关闭**（16:18 后新增）：
    - **功能语义**：`networkPolicy.allow.<domain>.[{forwardURL}]` 由 Vercel 基础设施代理转发（执行点非 guest netns）；强制 https、拒 query/fragment、拒 userinfo、拒 http；原始路径经 `Vercel-Forwarded-Path` 头透传
    - **执行点指纹**：UA=curl/8.18.0；向任意公网目标附加 `Vercel-Sandbox-Oidc-Token`（aud=forwardURL 完整 URL）+ Vercel-Forwarded-Host/Path/Port/Scheme；可达 Vercel 边缘（不存在 deployment → 404 DEPLOYMENT_NOT_FOUND）
    - **SSRF 面关闭**：私有/回环/链路本地/CGNAT 全 502 且 guest 内明文+TLS 监听器（127.0.0.1:8080/8443、eth0 100.64.30.216:8443）零连接 → 连接级私有地址防护；对照：公网 IP 直连正常（1.1.1.1→301、8.8.8.8→302）→ 502 ≠ IP 拦截，纯私有地址防护
    - **变体全拦**：127.0.0.1、[::1]、localhost、127-0-0-1.nip.io、十进制 2130706433、169.254.169.254、metadata.google.internal、guest eth0 IP（100.64.x.x）
    - **API 面关闭**：forwardURL=https://api.vercel.com/v2/user|/v2/teams → 403 missing token（OIDC 不作为 Authorization）→ 无认证绕过；OIDC 自动附加属 B.7 credential brokering 设计延伸
    - **transform 头注入**（v47）：自定义头（X-Inj-Mark）可注入转发请求，配置者自控，无跨租户价值
    - 证据：_x_transform.py/out（v47 注入）、_x_transform2.py/out（v48 语义+私有目标）、_x_transform3.py/out（v49 对照+监听器）、_x_transform4.py/out（v50 IP直连+api+eth0 IP）
11. **v45-v46 SDK/fs/ports/PTY 系列 → 全部面关闭**（18:40 重新归档，细节核对版）：
    - **v45c 跨租户矩阵 → 全隔离**（_x_team_x_out.txt 实测 5 项）：P1 attacker token+victim team+victim project 创建→403 Not authorized；P2 attacker team+victim project→404 Could not find project；P3 attacker token+victim team+own project→403；P4 victim token DELETE attacker sandbox→404 且 verify 200（sandbox 完好）；P5 attacker token+fake team→403
    - **v45e/f fs/read|write → guest 内解析（决定性）**：guest 写 marker（sudo tee /etc/hostname、/vercel/fs_marker.txt、touch /tmp/guest_tmp_mark）→ fs/read /etc/hostname→HIT-MARK!guesthostname、/vercel/fs_marker.txt→HIT-MARK!FS_MARK_XYZ、/tmp/guest_tmp_mark→200（空文件存在）、/../../../../etc/hostname→HIT-MARK；**/etc/passwd→200 无 HIT（响应 600 字符截断，marker 追加在文件尾未显示，非逃逸证据）**；fs/write 方法变体（PUT-json 404、POST/PUT plain/noc/oct 全 415）→ 仅 gzip tar + x-cwd 可用（v46b：/tmp 成功、`../../` 文件名被拒 "Removing leading ../../"）→ 无 host 写原语
    - **v46e ports 路由 → 设计功能**：创建带 ports 的 sandbox → 公网 `https://sb-{random}.vercel.run`（无服务时 502 SANDBOX_NOT_LISTENING）；wss 端点 token 仅在 `?token=` query 有效（Authorization header 401，无 token 401）
    - **v46f/g/h PTY 协议 → 未打通（无价值）**：interactive 返回 `wss://sb-*.vercel.run/ws/interactive` + `__xmm` 前缀 token，多次调用 URL/token 稳定复用；wss 握手 101 成功但 8 种 JSON/raw 消息变体（input/cmd/data/shell/pty/run/resize）全 TIMEOUT 无响应；guest 内 23456 与 26661 均监听（Go "404 page not found"），常规路径枚举（/ /healthz /metrics /debug/pprof/ /api /v1 /version /info /ws /shell）全 404 → 服务对 HTTP 探测封闭，PTY 协议无文档难逆向，面关闭
    - **v46 SDK 端点全集 → 无新漏洞**：extend-timeout 校验（0/-1 拒绝）、kill 需 signal 数值（=9 200 但 exitCode=null）、fork 数据复制正常（v46c）、PATCH networkPolicy deny-all 生效、v3 create 200、fs/read cwd 参数不影响解析、interactive 跨租户 404、fs/write 跨租户隔离（v46b）
    - **配额 402 解锁（重要运维教训）**：快照存储配额超限（Hobby ~7GB）导致 create 402 payment_required；根因 = 11 个 642MB 自动快照（stop 自动创建，DELETE sandbox 不删快照，快照独立于 sandbox 存在直至过期/删除）；解法 `GET/DELETE /v2/sandboxes/snapshots?teamId=&project=` 清理 created 快照（deleted 状态 400 无需删）→ 配额恢复。**教训：避免频繁 stop；删除 sandbox 后必须清理快照**
    - 证据：_x_team_x.py/out、_x_fs_api.py/out、_x_fs_api2.py/out、_x_ports.py/out、_x_ws_shell.py/out、_x_pty2.py/out、_x_sdk_api.py/out、_x_sdk_api2.py/out、_x_sdk_api3.py/out、_x_interactive.py/out、_x_pty.py/out、_x_pty3.py/out、_chk_snaps*.py
12. **v45d POST 枚举 + snapshot 生命周期 → 面关闭**（18:40 重新归档，细节核对版）：
    - **POST 子资源枚举**：exec/exec-sync/execSync/restart/pause/resume/kill/upload/logs/events/stream/env/info 全 404（无此端点）；fs/read（400 missing path）、fs/write（415 无 ctype）已测过；**`POST /v2/sandboxes/sessions/{sid}/snapshot` → 201 手动快照**（snap_xxx，sizeBytes≈642MB）——官方 REST API（/docs/rest-api/sandboxes/create-a-snapshot），非隐藏端点
    - **policy body 变体 → 校验严格**：mode=null→400 "should be string"、mode=空/weird→400 枚举校验、allowedDomains=字符串→400 "should be array"；无 fallback allow-all 漏洞
    - **snapshot 201 → sandbox 自动停止（实测 + 官方文档证实设计行为）**：cmd 基线 alive → POST snapshot 201 → t+2s running → t+5s stopped → cmd 全 410。官方文档："Once you create a snapshot, the sandbox shuts down automatically and becomes unreachable"。**resume 恢复（实测）**：GET sandbox?resume=true → 200 返回 currentSnapshotId + 新 sessionId（旧 sid 永久失效）→ status=running；新 sid 验证：快照前写入文件存在、快照后写入文件不存在（数据回滚到快照时刻，标准 checkpoint 语义）
    - **snapshot 跨租户（写入方向 IDOR）→ 隔离正确**：attacker token 对 victim session POST snapshot → 404 "Vercel Sandbox not found."（victim 自己 GET 200 对照确认 sandbox 存在）；读方向 v44s 已证 404
    - **stale sessionId → 410**：stop 后旧 sid 调 cmd → 410 sandbox_stopped（正确失效）
    - **列表 API 细节（对照实验）**：`GET /v2/sandboxes/snapshots` 的 limit 上限 50（limit=100 → 400 "limit should be <= 50"），与请求实现无关（api_raw 无 Content-Type 亦 200）；响应超 4KB 截断会破坏 JSON 解析（读取需 ≥20KB）
    - 证据：_x_post_enum.py/out（v45d）、_x_pol_stop.py/out（policy 复现：空 body 200 正常）、_x_snap_stop.py/out（snapshot 停止决定性）、_x_snap_resume.py/out（resume 恢复+数据回滚）、_x_snap_idor2.py/out（跨租户 404）、_chk_snaps3.py/out（清理）、_chk_lim.py（limit 对照）
13. **v51 官方文档 + SDK 源码驱动 → 全部面关闭**（19:05 归档）：
    - **create `source` 三型 → 拉取均在 guest 内（无控制面 SSRF）**：`type:snapshot,snapshotId` 跨租户→404 "Snapshot not found."（自用 200 对照，功能正常）；`type:tarball,url` deny-all→downloading failed exit6 vs 默认策略 httpbin→uncompressing failed exit2（下载成功解压失败）→ **受 guest networkPolicy 控制**；`type:git,url` deny-all→git clone failed exit128 vs allow-all→200；file:// 可用但 guest 视角；私有地址（127.0.0.1/169.254.169.254）全连接失败 exit7
    - **GET /v2/sandboxes/snapshots/{id} → 元数据无泄露**：id/sourceSessionId/region/sizeBytes≈642MB/expiresAt（确认 v4 默认 7 天过期）/creationMethod=manual
    - **fs/mkdir → 路径规范化正确**：`../mk_esc`、`a/../../mk_esc2`、`/tmp/../mk_esc3` 全 200 但均解析到 guest 根内（find 验证）；x-cwd 相对路径同样安全；无逃逸
    - **v3 snapshot/fork → 正常**：v3 快照 201 + fork 200（currentSnapshotId+新 session）
    - **GET cmd 列表跨租户 → 404**（自己 200：id/name/args/cwd/exitCode/durationMs，args 含完整命令）
    - **drives → private beta 403**："Drives are in private beta"（无权限，面关闭）
    - **ports 内部端口 → 防护到位**：ports:[23456]→400 reserved_port（显式保留）；26661（interactivePort）可配置但 guest 内无监听（host 侧代理）→ 公网转发 502 SANDBOX_NOT_LISTENING；23457 同 502
    - **PATCH 新字段 → 正常配置**：runtime（node22/24/26/python3.13）、persistent、snapshotExpiration（0=禁用过期）、keepLastSnapshots（count 1-10+deleteEvicted）、failoverRegions、?resume=true
    - **SDK 源码唯一新端点 getSnapshotTree → 隔离**：`GET /v2/sandboxes/snapshots/tree?project=&snapshotId=`（文档未列）；自己 200（anchor+siblings+count）；跨租户 project→404 Could not find project；victim snapshotId+own project→200 空树；无 snapshotId→400 required；snapshotId 长度≥32 校验
    - **SDK 参数细节 → 均正常**：cmd `sudo:true`→root 执行（uid 1000→0，guest 内设计功能）；fs/read body cwd 与 header x-cwd 一致（../../../../ 规范化到根）；openInteractive POST→{url:wss://sb-*.vercel.run/ws/interactive, token:xxx}（需 API 鉴权，设计功能）；kill signal 需数字（字符串 400）
    - 证据：_x_src_snap.py/out、_x_src_tar.py/out、_x_src_git.py/out、_x_mk_esc.py/out、_x_snap_tree.py/out、_x_ports_int.py/out、_x_ports_26661.py/out、_x_sdk_params.py/out
14. **v52 残余面 + CIDR/IPv6 + CLI/OpenAPI 核对 → 全部关闭**（20:40 归档）：
    - **image 参数 → 内部镜像 only**：默认 `vercel/sandbox/universal@sha256:...`；nginx/docker.io/ubuntu → 404 "Image not found."（不拉 Docker Hub）；URL/registry 格式 → 400 "Invalid image reference"（无 SSRF）
    - **ports host 端口 → 纯 guest 转发**：2375/2376/9000/5432 均可配置但全 502 SANDBOX_NOT_LISTENING（guest 内无监听，不触 host）
    - **23456 协议确认 → Go http2 (h2c) 服务**：--http2-prior-knowledge 返回 "HTTP/2 404"（非 gRPC，grpc.health 404）；guest 内 26661 **Connection refused**（host 侧 VSOCK 代理端口，解释 ports 转发 502）；PID1 = `sandbox-init --socket=init.sock --pubkey=...`（ubuntu 用户，init.sock 签名面已提交 N/A）
    - **CLI 源码 → 无新端点**：vercel CLI sandbox 命令 = sandbox npm 包 = @vercel/sandbox 2.2.1（与 3.2.1 方法一致，仅少 forkSandbox）+ UI 层
    - **custom 模式 CIDR/IPv6 → 无绕过（决定性）**：allowedCIDRs/deniedCIDRs 仅限 custom 模式（deny-all/allow-all 下 400）；allowedCIDRs:["0.0.0.0/0"] 放行全部 IPv4（设计语义：CIDR 白名单 bypass 域名限制）；重叠 CIDR → 400 "allowed CIDRs overlap"（校验存在）；**IPv6 全拦**：custom+白名单下 -6 访问白名单域名仍 DNS 失败/连接失败，-4 正常（IPv6 不松于 IPv4，无 bypass）
    - **CIDR 服务端 bug（无安全影响，不提交）**：create + allowedCIDRs:["128.0.0.0/1"] → 500 "unexpected internal error"（0.0.0.0/1 正常；疑似 uint32 0x80000000 超 int32 有符号转换）；**PATCH network-policy 同值 → 200 成功**（仅 create 路径崩溃，用户可用 PATCH 设置同样值 → 无限制绕过）；PATCH 后无 fail-open（策略保持，example.com 仍拦）
    - **OpenAPI spec 核对 → 24 个 sandbox 端点全覆盖**（openapi.vercel.sh）：与文档目录一致；SDK 独有的 snapshots/tree 也已测 → 无遗漏端点
    - 证据：_x_img_ports.py/out、_x_grpc_probe.py/out、_x_cidr_bypass.py/out、_x_v6_bypass.py/out、_x_cidr_500.py、_x_patch_fail.py/out、_openapi_sandbox_paths.txt
15. **v53 virtio/内存设备面（方向 1：EC2 host 逃逸）→ 全部关闭**（21:40 归档）：
    - **virtio 设备集 = 标准 5 件**：virtio0/1=blk（vda 35GB root 镜像 + vdb 64GB 工作盘挂 /，启动时 vdb 从 0 扩容）、virtio2=net、virtio3=vsock、virtio4=rng；**无 balloon/console/mem/fs/gpu**（drivers 目录含 virtio_balloon/console/mem 驱动但无设备）→ 无额外设备面
    - **传输 = 纯 virtio-mmio**：kernel cmdline `pci=off` + 5 个 `virtio_mmio.device=4K@0xc0001000-0xc0005000:irq5-9`；dmesg "PCI: Fatal: No config space access function" → 无 PCI 配置空间；iomem 设备区 LNRO0005:00-04 与命令行一致
    - **/dev/mem 行为（STRICT_DEVMEM 正确）**：System RAM 全拒（0x100000/0x10000000/0xbffff000/0x100000000/0x156d0000 → EPERM）；非 RAM 可读（0xc0000000-0xeebfffff 空洞全 0、设备区、0x9fc00 Reserved）→ 无 host 泄漏
    - **AMZNC10C VMCLOCK（核心发现，标准设备无攻击原语）**：DSDT 解码 `\\_SB_.VCLK` HID=AMZNC10C CID=VMCLOCK _DDN=VMCLOCK _STA=0x0f _CRS=4KB@0xde000；0xde000 读回 "VCLK" magic+size 0x1000+ver1 flags 0xff+seq 0x300（host 预置静态结构）；**UAPI Group vmclock 规范 + Firecracker 1.15.0 标准特性**（非 Vercel 特有）；写测试：写 0xdeadbeef/0/0xffffffff 全成功读回（guest 可写）；**11s 观察零变化 + 写后 3s 不被 host 覆盖 → 无 host 交互/无更新 → 规范结构全数值字段无指针 → 无攻击原语**
    - **VMGENCTR（VM_Gen_Counter）**：SEV 代数计数器，无 MMIO 无 _CRS → 无面
    - **ECAM 0xeec00000（MCFG 声明）→ 全 0 未实现**（pci=off 下无 PCIe 配置空间）；LAPIC 0xfee00000 读全 0、IOAPIC 0xfec00000=0x19（标准模拟）；memmap 确认 4 段（RAM 0-0x9fbff/0x100000-0xbfffffff/0x100000000-0x156cfffff + Reserved 0xeec00000-0xfebfffff）
    - **MSR → guest 值无泄漏**：EFER=0xd01/LSTAR=0xffffffff81000080/SYSCFG=0/SYSENTER_EIP=0xfffffe0000003000（KVM 虚拟化值）
    - **ioport 全 16KB 扫描 → 纯标准设备**：仅 0x20=0xf4（PIC1）/0xa0=0x03（PIC2）/0x61=0x20（PPI）/0x64=0x10（8042 状态）/0x3f9=0x05（UART IER）；未模拟端口读回 0；0x80 写测试无状态；RTC 0x70/0x71 无响应
    - **信息泄漏（低价值）**：kernel cmdline 含 `build_version=2026.08.27-aed1eea...`（sandbox 镜像构建版本）+ `cell_id=hvc_iad1_...`（Vercel 内部单元 ID，guest 可见）→ 内部标识信息，无利用路径
    - **结论**：guest 可访问的全部设备/内存/IO/MSR 面均为标准 Firecracker 设备集 + 标准 ACPI（FIRECK 签名）；无额外设备、无 host 错误映射、VMCLOCK 静态无交互 → **无 EC2 host 逃逸路径，方向 1 关闭**
    - 证据：_x_v53_enum.py/out、_x_v53_mem.py/out、_x_v53_acpi.py/out、_x_v53_clk.py/out、_x_v53_obs.py/out、_x_v53_io.py/out
16. **v54 SDK 参数深挖 + 快照存储层 → 全部关闭**（22:10 归档）：
    - **PATCH currentSnapshotId 跨租户 → 404（隔离）**：attacker PATCH 自己 sandbox currentSnapshotId=victim 快照 → 404 "Snapshot 'snap_xxx' not found."（资源级授权；v51 只测了字段存在性，本次补跨租户引用）；victim 快照数据无法被 attacker resume 恢复（marker 验证设计）
    - **deleteOrphanSnapshots 跨租户 → 403（隔离）**：attacker DELETE victim sandbox + deleteOrphanSnapshots=true → 403 "Not authorized"（不走绕过路径），victim 快照完好（GET 200 对照）；自己账号 DELETE+orphan → 200 正常（orphan 清理语义）
    - **快照存储层无 URL 暴露**：SDK 验证器 Snapshot 结构（id/sourceSessionId/region/regions/status/sizeBytes/expiresAt/createdAt/updatedAt/lastUsedAt/creationMethod/parentId）无 URL/存储字段；GET 详情响应同样无 → 快照数据仅后端内部读取，无直接下载面
    - **runtime 参数**：v4 create 拒收（400 "should NOT have additional property `runtime`"）→ 仅 v2 create/PATCH 支持（设计功能，镜像差异不影响隔离边界）
    - **persistent 生命周期 → 正常**：create persistent=true 200 + 字段回显；PATCH false/true 切换正常；DELETE 后 GET/resume 全 404（persistent 不复活已删 sandbox，无对象生命周期漏洞）
    - 证据：_x_v54_base.py/out（基线：自己快照 PATCH/resume 正常）、_x_v54_x.py/out（跨租户决定性）、_x_v54_rt.py/out（runtime/persistent）

## 结论（08-30 全部面关闭，无新可提交漏洞）

今日验证：Exec 线（dup H1-3972961 根因）、v43 RCE 链（dup）、UDP 出网（无 bypass）、快照 IDOR（隔离）、跨沙箱共享写（COW）、策略持久化 stop/resume（正常）、跨租户写操作（全 404）、端点枚举（无新端点）、forwardURL SSRF（连接级私有防护）、fs API（guest 内解析）、跨租户全矩阵（隔离）、PTY/ports/interactive（设计功能）、snapshot 端点（官方设计：创建后自动停止+resume 从快照恢复；跨租户读写双向 404）、v51 文档/SDK 面（source 三型 guest 内拉取、getSnapshotTree 隔离、fs/mkdir 路径安全、ports 内部端口保留、cmd sudo 设计功能）、v52 残余面（image 内部镜像、CLI 无新端点、IPv6 全拦无绕过、CIDR 128.0.0.0/1 create 500 无影响、OpenAPI 24 端点全覆盖）、v53 virtio/内存设备面（标准 5 设备集、AMZNC10C VMCLOCK 标准静态无原语、/dev/mem STRICT_DEVMEM 正确、ECAM 未实现、ioport 纯标准、无 host 逃逸路径）、v54 SDK 参数深挖（PATCH currentSnapshotId 跨租户 404、deleteOrphanSnapshots 跨租户 403、快照存储无 URL 暴露、persistent 删除后不可复活）。

**合格标准（EC2 host 逃逸/跨租户/新 host 写原语/firewall bypass+exfil）今日无突破。** virtio/内存设备面（方向 1）已实测关闭，无 EC2 host 逃逸路径；剩余窗口 1 天，可选换产品线方向（需用户确认）。

## 证据文件索引（今日）
- skills/out/vda43_chain_evidence_guest_20260830_152557.txt（v43c RCE 链证据：marker/caps/seccomp/netns）
- skills/out/udp44_denyall_20260830_154403.txt、udp44_allowall_20260830_154431.txt、udp44_custom_20260830_154508.txt（UDP 三模式）
- _x_snap_idor.py 输出（快照 IDOR 404）
- _x_share_test.py 输出（COW 隔离）
- _x_pol_persist.py / _x_pol_resume.py 输出（策略持久化正常）
- _x_xwrite.py 输出（跨租户写全 404）
- _x_endpoints.py 输出（无新端点）
- 关键脚本：vda44_udp_probe_guest.py、_run_v44u.py、_x_*.py

## 环境
- TEAM=team_GIy1SZ444lspqeNbh4r8uAUg, PROJ=prj_iyw2xfjP3RKPT7n8b8c1tBIxxK5F, token=vercel_cookies.txt
- 驱动：skills/non-traditional-vuln-hunting/vercel_driver.py（api/cmd/fresh_sandbox）
- 输出：skills/out/；报告：vercel_report/

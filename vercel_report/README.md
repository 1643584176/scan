# Vercel Sandbox 逃逸报告归档（报告 1、报告 2 均已证伪）

## 报告 1：宿主盘读写（已撤回 2026-08-21）

- **提交日期**：2026-08-20
- **标题**：Vercel Sandbox escape: user code can read/write the host rootfs block device /dev/vda
- **严重度**：CRITICAL（预检确认 CVSS 9.3）
- **弱点**：CWE-653 Improper Isolation or Compartmentalization
- **状态**：**已主动撤回（Not a vulnerability，2026-08-21）**
- **撤回原因**：j171 跨沙箱验证证伪“写宿主磁盘”声明——j169/j170 在沙箱内写 /dev/vda 512B + fsync（成功）后，**全新沙箱读同一块完全读不到写入**（全零）→ /dev/vda 是每沙箱私有视图（只读镜像层 + COW，j120/121 已预告），写只影响自己、不跨沙箱，不存在“persistent across sandboxes / host RCE”。
  - 剩余能力（读 /dev/vda 内容）：读到的是镜像/快照视图内容，无敏感资产（前 2GB 无 shadow/SSH 私钥、ca-key.pem 未找到、celld.toml 仅为已删除残留）→ 按 Vercel 挑战规则（需真正逃逸/凭据窃取，“仅到 guest OS 不算”）不构成漏洞。
  - **验证方法教训**：j37b 的“写→fsync→读回一致→还原”只能证明写私有副本生效（COW 陷阱），无法区分写宿主与写副本；提交前必须做跨实例验证（沙箱 A 写 → 沙箱 B 读）。

## 报告 2：init.sock 签名绕过（已证伪 2026-08-21，建议撤回）

- **提交日期**：2026-08-20
- **标题**：Vercel Sandbox escape (2): init.sock signature bypass → arbitrary root command execution
- **严重度**：CRITICAL
- **弱点**：CWE-347 Improper Verification of Cryptographic Signature（采纳 H1 预检建议）
- **状态**：已提交，等待 triage → **2026-08-21 再检验证伪，建议主动撤回**
- **表单**：Asset=Vercel sandbox (OTHER)；Vulnerability Class=Cross-Tenant data access；Sandbox ID=sbx_WEaj1EnUQlA8FguQiaB26FmdmQED；Team/Project=标准测试资源
- **核心**：沙箱内代码 ptrace patch 沙箱 PID 1（sandbox-init）签名验证 3 个失败分支 → 任意 x-signature 通过 → Spawn 任意命令（全套 caps，可 setuid(0) root）

**❌ 证伪结论（2026-08-21，K2 对照实验 + j167/j168 + 报告 1 撤回联动）**：
- 签名绕过获得的 Spawn 能力（全 caps、setuid root）= 沙箱内普通进程**已有能力**（K2 实测：无 sudo 普通进程 CapEff=000001ffffffffff 全 caps、sudo -n id=root，与 j83 一致）→ 无新增权限
- 报告 2 最重 Impact（宿主 rootfs 持久化读写）依赖 /dev/vda=宿主盘，已被报告 1 撤回证伪（COW 私有副本，j169-171）
- j167/j168：纯 PTRACE_ATTACH 触发 sandbox_stopped，攻击前提当前不可复现（疑似 Vercel 修复或节点差异，未证实）
- 按 Vercel 规则（需真正逃逸/凭据窃取；仅到 guest OS 不算）→ 不构成漏洞，与报告 1 同因撤回
- **提交前检验缺失教训**：提交时未做"能力对照"（被绕过保护的能力 vs 攻击者已有能力）；且 j83（8-20 晚已标注"报告 1/2 的放大器，非独立漏洞"）后未当天触发报告复查——此二条已沉淀为强制规则

## 漏洞核心（报告 1）【已证伪，仅供历史参考】

沙箱 /dev 暴露块设备 /dev/vda（254:0），沙箱自身 rootfs 是 /dev/vdb（254:16）。沙箱内 root 进程可 O_RDWR 读写 vda（写 512B → fsync → 读回一致，已无痕还原）。

**判据实锤**（三证据，技术事实仍成立）：
1. 设备号：vda 254:0 / vdb 254:16
2. mountinfo：bind-mount 源来自 254:0（/etc/hosts、/etc/resolv.conf、/volumes/run/vercel/share、/run/cell/ca-cert.pem）
3. 沙箱内 /run/cell、/volumes、/opt/vercel 全部 NOT FOUND（只通过裸设备可达）

**❌ 证伪结论（2026-08-21，j169-j171）**：
- vda 是每沙箱私有视图（只读镜像层 + COW，j121 已预告），**写不跨沙箱**（j170 写+fsync → j171 新沙箱读块全零），不存在宿主写/持久化影响
- 旧结论“非 COW 假写”（j37b）判断错误：写后读回一致仅证明写私有副本生效，无法区分宿主/副本（COW 陷阱）
- 读的内容含宿主 rootfs 痕迹（XFSB、镜像文件、celld.toml 删除残留）但**无敏感资产**（无 ca-key.pem、无凭据）
- 按 Vercel 规则（需 Live PoC 的真正逃逸/凭据窃取；仅到 guest OS 不算）不构成漏洞 → 主动撤回

## 证据文件

| 文件 | 内容 |
|---|---|
| H1-vercel-sandbox-host-disk-access.md | 提交用精简报告（英文） |
| exp_j36_out.txt | 设备号对比 + mountinfo + 沙箱内不可见性 + vda 特征搜索（英文标签版，与原始输出逐字节一致） |
| exp_j37b_out.txt | 写测试完整证据链：O_RDWR → write 512 → fsync → READBACK True → RESTORE True【⚠️ 结论已被 j171 证伪：仅证明写私有 COW 副本，非宿主盘】 |
| H1-vercel-sandbox-init-sig-bypass.md | 报告 2 草稿（英文，待提交） |
| init_sock_bypass.py | 报告 2 利用工具（端到端验证通过；⚠️ 能力=已有，已证伪） |
| k2_run_out.txt | 报告 2 证伪对照实验（exp_k2.py）：PLAIN_CAP=000001ffffffffff（普通进程全 caps）、SUDO_ID=uid 0(root)、SUDO_CAP=全 caps → Spawn 能力=沙箱内已有能力 |
| exp_j65_sig_bypass_first_ok.txt | 免签名 Spawn 首次成功（id 执行） |
| exp_j75_service_enum_pidfd.txt | 服务枚举（Ping/Kill/Spawn 存在）+ pidfd_getfd 复制 fd |
| exp_j76_ping_kill.txt | Ping/Kill 语义 + Kill 杀进程验证 |
| exp_j77_control_nopatch.txt | 未 patch 对照：invalid signature |
| exp_j78_tool_e2e.txt | 独立工具端到端验证（开箱即用） |

## 实验脚本（保留在项目根目录）

- exp_j36.py — vda 身份验证
- exp_j37.py / exp_j37b.py — 写能力测试（j37 首版 pattern 长度 bug 误报 WRITE_IGNORED，j37b 修正）

## 相关实验链（J 系列，根目录）

exp_j26（0.1GB 首扫）→ exp_j30（0-100MB PAT 重扫）→ exp_j31/31b/31c（ext4→XFS 大端识别）→ exp_j32/33/34/35（inode 1042-1044 解析，celld.toml/xkernel.toml 定位，data fork 前 16B 动态混淆未破）

## 未解决线索（备用弹药，triage 要求补充时用）

- vda 上 ca-key.pem（vercel-proxy-ca 私钥）未找到 —— 找到可升证据强度（mount 被拒，仅能块设备慢扫）【⚠️ 报告 1 已撤回（2026-08-21），该线仅当发现真实 CA 私钥时才有独立报告价值（凭据窃取面）；现有多轮扫描（j73/j80-82/j122-123）均无私钥证据】
- ~~celld.toml/xkernel.toml 内容被动态混淆~~ 已解决（exp_j74）：inode 1043/1044 是 extents 格式，数据分别在物理 0x8D000/0x8E000；celld.toml = journald 日志采集配置（vector 格式），xkernel.toml = 内核日志采集配置
- /opt/vercel/celld-init.sh 的文件级定位（宿主 RCE 链理论可行，未实测；vda 上无 /opt/vercel 目录）
- 宿主 rootfs 前 2GB 扫描无 shadow/SSH 私钥（exp_j73）→ vda 是宿主管理组件盘（2.2GB XFS），非完整 OS；密钥面在宿主另一存储（未达）
- sandbox-init 控制面流量监听（pidfd_getfd 复制 fd 后只读观察）——宿主空闲时无流量，触发时机未摸清

## 2026-08-20 新线侦察结论（exp_j79-85，无新报告）

| 线 | 结果 | 判定 |
|---|---|---|
| 未 patch 沙箱进程全 caps（CapEff=000001ffffffffff 全开，uid 1000） | 实锤（j83） | 报告 1/2 的放大器，非独立漏洞；mount 被拒（seccomp） |
| /proc/1/root 穿透 mount ns 读宿主 PID1 视图（/opt /vercel /root 被 shell 空目录覆盖） | 可读可写（j79/80/81/82） | 读：无敏感数据（git/node runtime/npm 缓存）；写：per-cell 无跨沙箱影响；不构成报告 |
| 宿主 rootfs 结构 | Amazon Linux 2022/2023 容器；PID1 rootfs=vdb + vda bind-mount(/run/vercel/share、CA)；shadow 全 lock 无哈希；无私钥（j80/81） | 补充证据 |
| 跨沙箱 Kill（未 patch 沙箱 Kill 其他沙箱进程） | **假阳性**（j85 对照推翻）：spawn 进程生命周期绑定 cmd 会话，会话结束即消失；B 杀的是已不存在的进程 | 不提交 |
| 方法字典枚举（8 service × 38 方法） | 仅 SpawnService/Ping、Kill 免签名（空响应，无参数面）；其余 404 或签名保护（j79） | 无新面 |
| 沙箱重启/持久化链 | 无重启端点（sessions/start/stop/restart 全 404）；stopped 沙箱 cmd 返回 410；persistent 磁盘未验证到重启路径（j82/83） | 无新面 |

## 2026-08-20 第二轮新线侦察（exp_j86-108，无新报告）

| 线 | 结果 | 判定 |
|---|---|---|
| 网络策略（custom+allowedDomains）对 spawn 进程 | SNI 精确白名单（大小写/子域/后缀注入全拦截 j90）；代理按 SNI 转发完全忽略目标 IP（j89 决定性）；metadata RST 专门防护 | 设计完整，无绕过 |
| 数据面 ACL 矩阵（TCP/UDP/HTTP/TLS） | TCP connect 全通但数据首包 RST（按 IP 丢包）；UDP 仅内网 DNS 响应；TLS 矩阵暴露 awselb 503 → 代理按 SNI 转发（j87-89） | 收敛 |
| 宿主内部服务面（共享 net ns） | TCP 30001/30002/23456 OPEN 无 banner；Go net/http 特征（404+nosniff）+ HTTP/2 SETTINGS；路径字典全 404，非 spawn 服务，二进制在宿主节点不可见（j91-98） | 无可用面 |
| 宿主 unix sockets（cell/containerd/metrics/apm） | /proc/net/unix 可见但 mount ns 隔离文件不可达；/proc/1/root 穿透同样 MISS（PID1 与沙箱同 mount ns）（j93/j100） | 无新面 |
| init.sock 双协议签名（**415/505 之谜**） | Spawn=200 签名校验；Ping/Kill=415（**grpc 注册**，grpc+json ctype 下返回 Grpc-Status:16 签名错误）；SpawnInteractive=505（**h2-only**，--http2-prior-knowledge 下 200+invalid signature）；GET unary 405 | 统一签名中间件，connect/grpc/h2 全无绕过（j101/102/106） |
| **j79 "Ping/Kill 免签" 假阳性修正** | 415 响应 body 为空 → j79 判定逻辑误判 NOSIG；实际是 content-type 不匹配，签名依旧强制 | 修正存档 |
| API 层权限模型 | team 越权 403 / project 404 / session 404 / snapshot 404；snapshot 详情仅元数据无下载端点；cmd 参数面（environment/workingDirectory/snapshotId）全 400 拒绝（j103-105/107） | 权限模型完整 |
| snapshot 面 | GET /v2/sandboxes/snapshots/{id} 详情（size/sourceSessionId/expiresAt 元数据）；列表可用；无 content/download/restore 端点 | 无数据面 |
| cmd 进程 environ | 14 变量全 CA 证书路径（AWS_CA_BUNDLE 等），无凭证；sandbox-init cmdline 暴露 --pubkey=（报告 2 已覆盖）（j107） | 无凭证泄露 |
| runtime 镜像隔离差异 | 创建参数 runtime 合法，错误消息泄露允许值列表（node22/24/26, python3.13, cua-ubuntu-xfce, walleye-python, blackbox-playwright, sandbox-ai-sh, sandbox-roocode(-noble), sandbox-yournextstore, sandbox-v0）；但当前 project 仅可用 node/python 4 种（j108），隔离配置完全一致（Amazon Linux、seccomp=2、mount 拒、unshare 可用、vda 可见、/proc/1/root 穿透、metadata RST） | 无差异攻击面 |
| /dev/vda 直读（open+read，不需 mount） | 实锤 XFSB 可读（j106） | 报告 1 复现，非新根因 |

## 2026-08-20 第三轮新线侦察（exp_j109-111，无新报告）

| 线 | 结果 | 判定 |
|---|---|---|
| init.sock 非 RPC 路径（pprof/metrics/healthz 全 404）+ POST 变体 | 仅注册的 connect/grpc 方法有响应；pprof/metrics 未暴露（j109） | 无新面 |
| 宿主内部服务 30001/23456 完整方法字典 | Go net/http 404 + nosniff；interactivePort 26661 入站面（沙箱内监听容器端口，仅本地回环可达？待确认） | 无新面 |
| **pidfd 复制 sandbox-init socket fd 捕获合法签名请求** | j110 首次失败（read fd 报 EINVAL）；j110b accept 竞争成功：完整捕获 432B 请求（POST /Spawn，X-Signature+X-Timestamp，Content-Length 36） | 捕获方法可行，但见 j111 |
| **签名重放矩阵（j111）**：捕获合法 sig 后 T1 原样重放 / T2 改 TS / T3 改 body / T4 随机 sig | T1 原样重放连接被立即静默关闭（b''）；T2-T5 全部挂起超时；新 body 的 Spawn 未执行（文件 MISSING） | **签名绑定 TS+body，重放被拒，无重放攻击面**（T1 被静默关闭疑似重放/nonce 检测；T2-T5 挂起语义未深究，线已关闭） |
| **快照恢复面（j112/112b）**：停止时自动快照（creationMethod=automatic，含磁盘数据：size 随写入内容变化 131KB），但①新沙箱不继承（同 project 不同名/name 复用/persistent true+false 全 MISS）②恢复端点全 404（start/restart/wake/resume/stop/reboot/startSession/restore/snapshot/download/export）③快照详情仅元数据（id/sourceSessionId/sizeBytes/expiresAt/creationMethod，无 URL/内容字段） | **快照数据只进不出 → 无跨沙箱持久化、无泄露面，不构成漏洞，线关闭**（注意：GET /v2/sandboxes 需 project 参数非 projectId；create 超配额返回 402；DELETE /v2/sandboxes/snapshots/{id} 可删快照） |
| **sandbox-init 二进制静态分析（j113）**：16MB Go 二进制（/run/vercel/share/sandbox-init，沙箱内可读）字符串层扫描 | 无 PEM/私钥/token/Bearer/apikey 硬编码；无 IMDS/内网路径字符串；源码路径泄露（/app/containers/sandbox-init/{cmd,gen/spawn,internal/auth,internal/service/{interactive,reaper,spawn}}）确认模块结构；grpc-web 支持；--socket/--pubkey 参数必填 | **二进制干净无凭据；静态分析线关闭** |
| **UDP/QUIC 通道（j114/115）**：网关 100.64.0.1，ARP 仅网关；UDP 矩阵（DNS 53/123/161/514/30001/30002/23456/26661/8080/8081 到网关/IMDS/内网/公网）全 timeout；QUIC 443 全 timeout；ICMP 全失败 | 唯一 UDP 响应=配置 nameserver 172.31.0.2:53，但对**所有**查询（公网/内网/PTR/CHAOS/ANY/AAAA）返回 REFUSED → 网关 DNS 拒绝策略（直连查询全拒，系统解析走其他链路） | **UDP/QUIC 无未策略化通道，DNS 无信息泄露，线关闭** |
| **interactive WebSocket 面（j116-118）**：发现 `POST /v2/sandboxes/sessions/{sid}/interactive` + `{}` → 返回公网 wss URL（wss://sb-{12字符随机}.vercel.run/ws/interactive）+ 32B 随机 token（per-session，重复调用返回同值）。认证矩阵：无凭据/错 token=401；token 绑定 session（跨沙箱双向 401）；沙箱删除后 502 失效；协议探测（raw/JSON 8 种格式）连接后无响应（需特定协议/先建 PTY） | **认证链完整无绕过；token 不可枚举；能力=已有 cmd（uid 1000）无放大；线关闭**（附赠：快照配额耗尽时 create 返回 402 payment_required，DELETE /v2/sandboxes/snapshots/{id} 可释放） |

## 2026-08-20 第四轮新线侦察（exp_j119-128，无新报告）

| 线 | 结果 | 判定 |
|---|---|---|
| **sandbox-init 跨沙箱共享性（j119）**：双沙箱 stat /run/vercel/share/sandbox-init → DEV 均为 65024（254:0），INODE 不同但内容 MD5 完全一致 | 初判 per-cell 副本；后续 j121 修正为**镜像层 COW 视图**（详见下） | 链方向修正 |
| **宿主路径泄露 + 镜像 COW 隔离（j120/121）**：mountinfo 泄露宿主 bind 源：`/volumes/run/vercel/share → /run/vercel/share`（rw, xfs /dev/root）、`/run/cell/ca-cert.pem → /etc/pki/...vercel-proxy-ca.pem`（ro）；rename 绕过 ETXTBSY 成功替换 sandbox-init（原+16B 尾部标记，可执行性不变），5 个新沙箱全部加载**原始镜像内容**（含同节点 C1 ino=125832488 也原始）→ **每沙箱视图 = 只读镜像层 + COW**，写只影响自己 | **模板投毒链不可行，宿主 RCE 链（经文件系统层）关闭**；附：沙箱 inode 为虚拟编号（j128 证实超出 XFS 容量范围） |
| **宿主多节点调度确认（j121）**：5 候选沙箱 sandbox-init 虚拟 inode 分组 = 125832488（节点X）/125832463（节点Y）/125832466（节点Z）→ 同节点共享同一镜像 | 沙箱随机调度多宿主节点 | 影响：镜像投毒需按节点，且已被 COW 隔离否定 |
| **宿主盘含沙箱镜像数据（j122-124）**：/dev/vda 前 10MB 命中 AWS CLI 文档/Python stdlib（Application Signals、statistics.py）→ 宿主盘上存储沙箱镜像文件；EC PRIVATE KEY/CERTIFICATE 命中均为镜像内容误报 | vda=33GB XFS（SB: bs=4096 agblocks=540544 agcount=16 inodesize=512 inopblock=8 rootino=1024）；vdb=32GB XFS | 镜像文件本身无凭据价值；可作 XFS 遍历验证素材 |
| **cmd 通道执行限制（j122-127）**：wait=True 有 ~30s 执行上限（超时杀进程返回部分输出）；wait=False 需 timeout≥100 且 logs=False，但沙箱空闲自动停止（410 sandbox_stopped）后台任务不持久 | 影响扫描策略：全盘 33GB 扫描需分片或后台持久化（不可行） | 改用 XFS 结构精准定位（j129 进行中） |
| **XFS 结构解析（j128）**：/dev/vda SB 解析成功（XFSB, bs=4096, agblocks=540544, agcount=16, inopblock=8, rootino=1024）；inode 容量=agcount×agblocks×inopblock=69M < 125,832,488 → **沙箱内 inode 为虚拟编号，不存在于 /dev/vda**；但 rootino 可定位 → 目录树遍历可行 | /dev/vda = 真实宿主 rootfs XFS | **XFS 目录遍历线开启（j129）**：从 rootino 遍历宿主文件系统，目标 /run/cell/ca-key.pem（报告 1 增强：宿主 CA 私钥） |
| 报告 1 增强线（进行中）：ca-key.pem 定位 — 旧线（块设备慢扫）受 cmd 30s 限制；新线（XFS inode 遍历）纯读秒级 | 未完成（j129 待运行） | 若命中 CA 私钥 → 报告 1 升级为"宿主 CA 私钥泄露（可签发任意证书）"【⚠️ 报告 1 已撤回，本线目标失效；仅当发现真实私钥才考虑独立报告（凭据窃取面）】 |

## 2026-08-24 第五轮新线侦察（exp_j280-286，/proc/1/mem 内存写入线，无新报告）

| 线 | 结果 | 判定 |
|---|---|---|
| **/proc/1/mem 无 ptrace 保护可读写（j280）** | O_RDWR 打开成功，可直接读写 sandbox-init (PID1) 内存；ptrace attach 触发 sandbox_stopped（j167/168）但 mem 直写不触发 | 新通道，但见下行 |
| **patch init 代码 → 免签名 Spawn（j282/282c）** | 写 0x77ba00（签名验证函数序言 lea rsp→xor eax,eax;xor ebx,ebx;ret）后，无 X-Signature 的 Spawn 请求成功执行任意命令；子进程不继承 init fd（仅 stdio pipe） | 能力=已有（报告 2 证伪原则：免签名 Spawn = 全 caps 普通进程已有能力，K2 实测）；无 fd 继承通道 |
| **init fd 身份识别（j283/284）** | fd 4=socket 监听 init.sock（ACCEPTCON 确认）；fd 7/8=accepted 连接；fd 9/11=pipe=cmd 通道（复制后读到自身输出）；fd 5/6/16=eventpoll/eventfd/pidfd | init fd 均为沙箱内部通道 + cmd 转发管道，无宿主 socket |
| **fd 7/8 对端身份（j284）** | SO_PEERCRED：peer **pid=0 uid=0 gid=0**（对端在另一 PID ns = 宿主 root 进程）；j110b 曾在这些连接捕获合法签名 Spawn 请求（432B）→ 宿主 agent 常驻连接 | 宿主 agent 控制面连接可被 pidfd 复制 |
| **宿主 agent 流量观察（j285）** | 复制 fd 7/8 非阻塞读 75s + 触发 interactive/snapshot API：**零流量** | agent 仅沙箱创建时发初始化请求，之后空闲无数据；触发 API 不产生 agent→init 流量 |
| **init vs 沙箱进程权限边界（j286，决定性）** | Seccomp=2/1filter、全 caps、NoNewPrivs=0、7 个 ns inode 全同、mountinfo 全同、environ 仅 CA 路径无凭证、uid/gid=1000 全同 | **init = 沙箱内进程，无任何特权边界差异；/proc/1/mem 可写无能力放大** |

**❌ 线关闭结论（2026-08-24）**：/proc/1/mem 无 ptrace 保护可写是新机制，但①patch init 获得的能力=沙箱已有（全 caps）；②init 与沙箱进程权限/ns/seccomp/mount 全一致；③唯一差异 fd 7/8（宿主 agent 连接）可复制但零流量、无泄露面；④init environ/mount 无敏感数据 → 按 Vercel 规则（需真正逃逸/凭据窃取）不构成漏洞，不提交。**教训沉淀**：发现"新机制"（mem 直写绕过 ptrace）后应先做能力对照（被改写对象 vs 攻击者已有权限）再投入触发/流量实验，本次对照实验（j286）本可前置到 j281 之前。

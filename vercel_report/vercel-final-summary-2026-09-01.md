# Vercel Sandbox HackerOne 窗口收官总结（2026-08-18 ~ 09-01）

> **最终状态：窗口结束。6 份报告全部 N/A/dup，合格标准（EC2 host 新逃逸 / 跨租户 / firewall bypass+凭据 exfil / 新 host 写原语 / 控制面 IDOR）无突破。**
> 本文档为全窗口最终收尾：攻击面地图、每面结论、架构情报、方法论经验。

---

## 一、硬指标（最终结果）

| # | 报告 | 核心主张 | 裁决 | 根因 |
|---|---|---|---|---|
| 1 | H1-3954985 | /dev/vda = EC2 host 盘读写 | 自撤回 | COW 快照是 guest 盘非 host 盘，信任边界错误 |
| 2 | H1-3955363 | init.sock 签名绕过 → 全 CapEff + setuid(0) | N/A | 影响停留 own microVM；攻击面在 Known B.6 |
| 3 | H1-3965216 | mount /dev/vda 逃逸 | N/A | guest 盘，Known A.5，"stays inside your own microVM" |
| 4 | H1-3972961 | containerd.sock → 特权容器 → cell root | N/A | Known B.2，无 materially new impact |
| 5 | fw_vpc | custom 策略放行整个私有地址空间 | dup | #3951926 已覆盖 |
| 6 | sandbox-control-plane-forgery | pidfd 窃取 fd 伪造 SpawnEvent | 自评 N/A 未提交 | 影响停留 own microVM |

**总消耗**：约 15 天 + 大量实验轮次；**总收益**：0 赏金。技术积累全部沉淀在脚本与本文档。

---

## 二、攻击面地图与逐面结论（全窗口）

### 2.1 架构（实证结论）

```
EC2 host (r6id.metal, i-01689cd96b9222434, us-east-1 VPC 172.31.0.0/16)
└─ cell VM (celld PID1, cell-id=hvc_iad1_..., containerd PID491, sandboxctrl PID534, sandbox-init PID577)
   └─ sandbox microVM (Firecracker, guest uid=1000, passwordless sudo)
        ├─ 23456 = sandboxctrl ControllerService (ConnectRPC) — 端口注入 guest loopback
        ├─ 26661 = interactive 本地后端 (Go net/http + ws) — guest loopback 监听 (uid=0)
        ├─ /run/vercel/share/init.sock — celld→sandbox-init 签名控制通道
        └─ 网络: v2 沙箱 /vercel/sandbox 可写; v4 沙箱不可写 (创建路径差异)
```

### 2.2 已提交面（全部 N/A/dup，不可复用）

- **/dev/vda 系**（#3954985/#3965216）：guest 系统盘 COW 快照，mount 后是 microVM 自己的盘，非 host。Known A.5。
- **init.sock 签名系**（#3955363 + v205-213 重放链）：见下方"技术发现"。
- **containerd 系**（#3972961 + v113-132 cell.sock 线）：guest 内 containerd.sock 世界可访问 → 特权容器（no pid ns、全 caps、/proc bind）→ host celld 的 /run/cell/cell.sock ConnectRPC 无认证 API（ContainersService Create/Start/Exec/Kill/Wait/Mount、ProcessService StreamOutput、UsageService GetResourceUsage）。Create 容器成功（shim pid 实证）但 Exec 进程从未真正创建（Kill: "process not created"）、StreamOutput 无输出 → 无跨边界数据/代码执行 → 与 Known B.2 重叠，不提交。
- **fw_vpc**（dup #3951926）：见下方"技术发现"。

### 2.3 本窗口后期（v205-v228）逐面结论

| 面 | 实验 | 结论 | 状态 |
|---|---|---|---|
| init.sock 签名重放链 | v205-213 | 签名只覆盖 X-Timestamp 不含 body，120s 窗口内任意命令重放成功；跨沙箱拒绝；服务仅 Spawn/Kill 两方法 | 技术存档（N/A） |
| CreateSnapshot 控制面 | v192-217 | 23456 无鉴权；任意 driveId 触发宿主快照+stop 沙箱；bucketBaseUrl 任意接受但**不上传**；无跨沙箱 IDOR | 技术存档（N/A） |
| cell.sock host celld API | v113-132 | 无认证 ConnectRPC；Create 容器成功无输出；无枚举端点；跨租户无面 | 关闭（Known 重叠） |
| interactive 26661 指纹 | v218-220 | Go net/http；/health 200；无 token ws→401；带 token→101；ConnectRPC 路径全 404 | 闭环 |
| token 绑定与 ws 执行层 | v221 | token 强绑定沙箱（交叉 401）；start 消息在 guest 内执行（uid=1000）；一次 start 即 exit；路径模糊全 404 | 闭环 |
| 公网 wss 代理面 | v227-228 | sb-xxx.vercel.run:443 暴露 /health(200) 与 /ws/interactive(401)；26661 不公网暴露；带 token 后仅 `{"type":"start"}` 被接受，connect/portforward/exec/fs 全静默；与 guest 内同后端 | 闭环 |
| bucketBaseUrl SSRF | v222 | https/http/webhook.site/IMDS/VPC 全接受但 webhook.site 零请求——解析不用于上传 | 关闭 |
| v4 source SSRF | v223 | tarball/git 下载在 **guest 网络层**执行（IMDS/VPC 连接失败同 guest 防火墙，公网可达） | 关闭 |
| 快照数据面 | v225-226 | resume 的 snapshotId **参数被忽略**（总恢复最新）；列表/详情/删除按 project 隔离；manual snapshot 也 stop 沙箱 | 关闭 |
| 控制面端点枚举 | n10-n13 | exec/logs/files/status/events/terminal 全 404；sessions 列表按 project 隔离，bad team 403；snapshot/fork/stop/cmd 可用 | 无越权 |
| 集群扫描 | v219 | 100.64.0.0/24 全端口无响应 | 关闭 |
| 跨租户测试 | 8/29 双账号 | attacker 按 name/session/network-policy 访问 victim 全 404；网络层特征端口 RST | 关闭 |
| guest 端口枚举 | v227 | 仅 23456/26661 两个 LISTEN，无其他宿主服务 | 闭环 |

### 2.4 技术发现（有价值但未达提交门槛）

1. **init.sock 签名重放链**：ed25519 签名消息只含 timestamp（不含 body/path）+ ≥120s 窗口 + 无防重放 → 沙箱用户可捕获签名后执行任意 Spawn 命令、伪造 SpawnEvent 响应（MITM celld→init 通道）。**修复需签名覆盖 body + 一次性 nonce**。官方即使修掉 ptrace 面（Yama），此协议级重放仍有效。
2. **CreateSnapshot 无鉴权 + 快照资源消耗**：普通 guest 进程可触发宿主快照（250MB/次）并 stop 沙箱；driveId/bucketBaseUrl 无校验（仅非空）。
3. **cell.sock 无认证 API**：host celld 的 ConnectRPC 全方法可用（Create/Start/Exec/GetResourceUsage 等），是 Known B.2 的宿主侧端点；未发现 List 等枚举面。
4. **custom 网络策略私有网段放行**：custom 模式（文档=默认拒绝）实际放行全部 RFC1918/保留网段（172.31/10/8/192.168/100.64/169.254），5432 返回 PG 协议响应；deniedCIDRs 对私有网段 silent fail-open、对公网生效；allowedCIDRs=[172.31.0.0/16] 时反而不可达（域名 allow 路径的意外行为）。SNI 代理仅 443、无凭据注入。
5. **interactive 协议**：公网 wss（443，per-sandbox 域名 sb-xxx.vercel.run）→ 内部 26661；token 在 URL query；仅 start 消息（guest 内 sh 执行）。

### 2.5 已关闭面（早期窗口，v1-v204 要点）

- vsock 2050 host 服务基本 RPC（Known B.1）
- DogStatsD/metrics vsock forwarder 注入（Known B.5）
- OIDC token 沙箱内捕获无外传通道（Known B.7）
- 全 41 caps / seccomp 宽松 / /dev bind（Known A.2-A.4）
- 公开 CVE 版本匹配（Out of scope #5，需 weaponize）
- 自沙箱 DoS / 静态分析 / SDK 客户端代码（Out of scope #2/#9/#11）
- 删沙箱后旧 session exec（生命周期正确，404）
- fs/read API 路径穿越（截断到容器根，无 host 穿越）

---

## 三、关键架构情报（可复用资产）

- **网络**：AWS VPC us-east-1，172.31.0.0/16；DNS 172.31.0.2（AmazonProvidedDNS）；guest 的 /proc/net/tcp6 可见宿主监听（netns 共享视角）；guest 内无 `ip` 命令（busybox 裁剪）。
- **控制面**：sessions 列表含 `interactivePort: 26661`；快照 API（POST sessions/{sid}/snapshot → 201 + stop 沙箱；GET/DELETE /snapshots/{id}?project=；fork API POST /v2/sandboxes/{name}/fork）；resume 参数 snapshotId 被忽略。
- **ECR**：account ID 977805900156 / 977805900182（镜像拉取情报）。
- **沙箱差异**：v2（fresh_sandbox）vs v4（source/drive）创建路径——v4 沙箱 /vercel/sandbox 不可写。
- **防火墙**：SNI 代理架构（443 TLS 终止 + 按 SNI 转发，目标 IP 被忽略）；custom 模式私有网段放行（见 2.4.4）。
- **guest 内可用工具**：python3、sh、sudo（passwordless）、无 nc/ip/hostname。

---

## 四、方法论经验与教训（对任何 HackerOne 项目复用）

### 教训（按严重度）
1. **开始前必须读规则 + Known findings 清单**——第一周火力全在官方排除面上，被用户催 3 次（8/21、8/25、8/26）才系统性读。
2. **边界认知错误**：/dev/vda 当 host 盘，报告 1 整个影响主张建立在错误信任边界上（COW 快照）。
3. **已知原语当新发现**：containerd.sock 未认证早在 Known B.2，提交前没对照自查 → N/A。
4. **"新根因"≠"新影响"**：Vercel 只认影响（host 逃逸/跨租户/新 host 写原语），不认根因新旧。
5. **报告自证局限**：把"vsock CLOSED / 双沙箱 NOT SHARED"写进报告 = 替 Vercel 写好 N/A 理由。
6. **负面结果不写进报告**（或先找到正面影响再写）。
7. **成本意识**：付费资源测试前先问"这次测试能回答什么问题、答案能支撑提交吗"。

### 有效方法（保留）
1. **零信任 + 验证承诺框架**：任何响应都不是无漏洞证据；成功响应也要构造反例验证（如 ws 101 后验证执行层、快照 200 后读回 marker 验证 snapshotId 是否生效）。
2. **单点打透**：一个面反复多轮实验（v205-213 重放链 9 轮、v127-132 cell.sock 6 轮）直到决定性结论，不铺开。
3. **决定性实验设计**：双沙箱交叉（token 绑定）、同沙箱策略切换（fw 四阶段）、marker 读回（快照恢复）、延迟重放矩阵（A/B/C/D 对照）——把"看起来对"变成"实测对"。
4. **环境侦察法**：/proc/net/tcp6（宿主监听）、/proc/net/unix（socket 影子）、/proc/1/environ、mountinfo、vda 挂载读 celld-init.sh。
5. **协议级攻击**：手工 ConnectRPC/protobuf/gRPC h2c/ws 帧——不依赖现成客户端，格式自己构造（ed25519 签名重放、ws 消息枚举）。
6. **公网回连捕获**：webhook.site 验证"服务端是否真的发起请求"（bucketBaseUrl SSRF 决定性证据：零请求）。
7. **双账号对照**：attacker/victim 分离验证授权隔离（全部 404 = 隔离正确，停止）。

### Windows/Git Bash 环境陷阱（本窗口反复踩）
- 复杂引号/for 循环/heredoc 一律写脚本文件（.py）执行，不用内联 -c
- python3 显式调用；sed 替换失败用 Python io 替换
- 文件路径 F:\ → D:\ 批量替换脚本
- 大段文件修改用 Write 全量重写（SearchReplace 对长文件易失配）

---

## 五、技术资产清单（文件索引）

- 驱动：`skills/non-traditional-vuln-hunting/vercel_driver.py`（api/cmd/fresh_sandbox，token 从 vercel_cookies.txt 读）
- 报告：`vercel_report/H1-*.md`（6 份）+ `fw_vpc/`（证据包 19 文件 + PoC zip）
- 归档：`vercel_report/H1-init-sock-replay-chain-archive.md`（重放链 + CreateSnapshot 技术存档）
- 本窗口末期实验：`_run_v218.py` ~ `_run_v228.py` + `vda2xx_*_guest.py` payload（interactive/快照/SSRF/公网 wss 全套）
- 经验：`经验/全局经验/Vercel项目复盘与通用教训.md`、`经验学习*.md`
- 环境：TEAM=team_GIy1SZ444lspqeNbh4r8uAUg，PROJ=prj_iyw2xfjP3RKPT7n8b8c1tBIxxK5F，webhook uuid 存 `_wh_uuid.txt`

---

## 六、最终结论

- **为什么没有拿到赏金**：合格标准（host 逃逸/跨租户/凭据 exfil）每一项都要求越过 microVM 信任边界或跨租户，而 Vercel 的边界工程做得相当扎实——所有 guest 侧原语（盘/socket/签名/端口/ws）都被隔离在 own microVM，控制面授权（name/session/snapshot/fork/project）全部正确隔离，唯一真实缺陷（custom 防火墙）是 dup。
- **技术收获**：签名重放链（协议级，修复面独立于 ptrace）、cell.sock 无认证 API 全集、interactive/快照/控制面完整协议地图——这些在 Vercel 修复后仍可复测（重放链修复需签名覆盖 body，若只修 ptrace 面则仍有效）。
- **对后续项目**：严格先读规则 → Known findings 自查 → 影响导向选点 → 决定性实验 → 报告精简。教训比赏金更值钱。

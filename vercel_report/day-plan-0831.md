# Vercel Sandbox 第 12 天作战记录（2026-08-31，窗口最后一天 09-01 结束）

> 会话压缩存档 | 最后冲刺 17:00-18:00（用户指令：6 点前出不来漏洞收工）

## 合格标准（官方 4 次重申）
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
| 5 | custom VPC bypass (fw_vpc) | dup of #3951926 |
| 6 | pidfd 控制面伪造 | 自评 N/A 未提交 |

## 今日最终冲刺：cell.sock（host celld ConnectRPC API）线 v113-v132 → 关闭

### 攻击链（复用 Known B.2 特权容器链）
mount /dev/vda（Known A.5）→ /mnt/vdax/run/containerd/containerd.sock（Known B.2 世界可访问）→
Containers/Create + Tasks/Create/Start（gRPC h2c 手工 protobuf）→ 特权容器（no pid ns、全 caps、/run /proc bind、chroot /mnt/g）→
payload 访问 **/run/cell/cell.sock**

### 关键发现（v127-v131）
1. **/run/cell/cell.sock = host celld 的 ConnectRPC API，无认证**（v119 发现，v127 证实普通 guest 无此 socket）
   - `vercel.hive.cell.api.containers.v1.ContainersService`：Create/Start/Exec/Kill/Wait/Mount
   - `vercel.hive.cell.api.processes.v1.ProcessService`：StreamOutput/Wait/Kill
   - `vercel.hive.cell.api.usage.v1.UsageService`：GetResourceUsage（200 `{"billableCpuTime":"1.769s"}`）
2. **特权容器 /proc = host /proc**（v128 决定性）：PID1=celld（cmdline 含 `--cell-id=hvc_iad1_b5d62a97_b280ffd2bf8544d3860bb6b3ffaa22bf`），proc 含 containerd(490)/containerd-shim/sandboxctrl(534)/sandbox-init(577)
3. **cell API Create+Start 在 host 创建真实 containerd 容器**（v128）：shim pid 685 `containerd-shim-runc-v2 -namespace default -id ctr_xxx -address /run/containerd/containerd.sock`，cgroup=/container/runtime，environ 含 cell_id
4. **Exec 时序窗口**（v113/v130/v131 复现成功）：Start 后 ≤0.1s 内 Exec → 200 `{"processId":"hvcp_xxx"}`；0.8s+ 后 → 500 "cannot exec in a stopped state"（容器 init 立即退出）
5. **StreamOutput**：json 变体全报 "only stdout or stderr can be requested"（字段名不对）；proto field2=1 → 200 + `{"error":{"code":"aborted","message":"context cancelled"}}`（流建立后取消）；field2=2 → NO_RESP 挂起
6. **ProcKill** → 500 "process not created: failed precondition"（Exec 进程从未真正创建）
7. **每次 Exec 在 host /proc 产生新 sh 进程**（v130 pid 653 / v131 pid 654），但 StreamOutput 拿不到输出
8. v129 Create 变体（process.args/command/args/proc-cmd/entrypoint/plain）全 200 但 Start 后无新 pid；v132 Exec 12 次重试全 500（时序未命中）

### 关闭判定
- cell.sock 无认证 API 属于 **Known B.2（host control socket 世界可访问）的延伸**——B.2 已覆盖"host control socket spawn 兄弟容器"，cell API 的 Create 能力与之重叠，**无 materially new impact**
- Exec 返回 processId 但进程从未真正创建（Kill: process not created）、StreamOutput 无输出 → 无跨边界数据/代码执行证据
- 未发现跨 cell/跨租户操作能力（ContainersService 无 List 等枚举端点，全 404；只有 Create/Start/Exec/Kill/Wait/Mount/StreamOutput/GetResourceUsage）

## 结论（08-31 最后冲刺结束）
cell.sock 线（host celld 未认证 ConnectRPC API）在 17:00-18:00 最后 1 小时深度挖掘（v127-v132 共 6 轮实验）后判定：**与 Known B.2 重叠、无 materially new impact，不提交**。
今日最终无新可提交漏洞。整个窗口（8/18-9/1）共提交 6 份报告全部 N/A/dup，合格标准（EC2 host 逃逸/跨租户/新 host 写原语/firewall bypass+exfil）无突破。

## 证据文件索引（今日冲刺）
- vda127p.py、_run_v127.py（普通 guest 无 cell.sock）
- vda128_probe_guest.py/guest.py、_run_v128.py（host /proc 决定性 + cell API 无认证 + shim 685）
- vda129_probe_guest.py/guest.py、_run_v129.py（Create 变体）
- vda130_probe_guest.py/guest.py、_run_v130.py（v113 时序复现 + StreamOutput 全变体）
- vda131_probe_guest.py/guest.py、_run_v131.py（双线程流时序：context cancelled 证据）
- vda132_probe_guest.py/guest.py、_run_v132.py（Exec 重试 + 进程解剖，未命中窗口）

## 环境
- TEAM=team_GIy1SZ444lspqeNbh4r8uAUg, PROJ=prj_iyw2xfjP3RKPT7n8b8c1tBIxxK5F, token=vercel_cookies.txt
- 驱动：skills/non-traditional-vuln-hunting/vercel_driver.py（api/cmd/fresh_sandbox；cmd 需自行构造 body 加 "sudo": True）
- 输出：skills/out/；报告：vercel_report/

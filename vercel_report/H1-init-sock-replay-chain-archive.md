# Vercel Sandbox 窗口收官 — init.sock 签名重放链 + CreateSnapshot 控制面 (2026-09-01)

> **状态: 技术存档(评估为 N/A, 未提交)** — 对照官方判定标准(#3955363 等):
> 影响停留 own microVM、攻击面(sandbox-init 控制面/签名密钥材料/全 CapEff)已在 Known findings、
> 无 EC2 host 逃逸/跨租户/防火墙或凭据控制绕过 → 不满足提交门槛。存档为技术记录。

## 发现 1: Spawn 签名只覆盖 X-Timestamp 不覆盖 body → 重放任意命令 (v205-v213 实证)

### 攻击链 (全链实证, 无需 ptrace/内存补丁)
1. 沙箱用户 (uid 1000, 默认账户) 有 passwordless sudo → `sudo mv /run/vercel/share/init.sock init.sock.bak`
2. 假 Unix socket 监听 (bind 到原路径), 等待下一个宿主命令 (`POST /v2/sandboxes/{sid}/cmd`), 40s 内必到
3. 捕获 celld 的合法 `X-Signature` + `X-Timestamp` (v205: 6 个完整请求捕获)
4. 恢复 socket (`sudo mv init.sock.bak init.sock`)
5. **120 秒窗口内** (v210 实证 60s/120s 延迟重放均执行成功) 直接连 init.sock 发送任意构造的
   SpawnRequest (protobuf: field1=command, field2=args, field4=cwd) + 捕获的 (ts, sig)

### 决定性证据
| 实验 | 内容 | 结果 |
|---|---|---|
| v208-A | 捕获签名 + 改 args (写 /tmp/v208_a) | ✅ 执行成功 `REPLAY-A-OK` |
| v208-B | 捕获签名 + **全新 body** (command=id) | ✅ 执行成功 `uid=1000(vercel-sandbox)` |
| v208-C | 改 ts (ts+1) | ❌ 与假签名基线响应相同 (签名拒绝) |
| v208-D | 假签名 | ❌ 拒绝 |
| v210 | 同沙箱 60s/120s 延迟重放 | ✅ 均执行 (窗口 ≥120s) |
| v209 | 跨沙箱旧签名 (12min 前) | ❌ 拒绝 (签名绑定沙箱上下文) |
| v213 | 原样重放 + 改 ts 对照 | ✅/❌ 同 v208; 签名验证在业务层 (HTTP 200 + connect 错误帧) |

### 根因
1. `X-Signature` (ed25519) 的消息只含 timestamp (+ 未知道沙箱上下文), **不含 body/path**
2. init.sock 权限 `srw------- vercel-sandbox` → 沙箱用户可替换 (sudo 可用)
3. 签名新鲜度窗口 ≥120s, 无一次性/防重放

### init.sock 服务枚举 (v213)
- `/vercel.sandbox.spawn.v1.SpawnService/Spawn` → 200 (存在)
- `/vercel.sandbox.spawn.v1.SpawnService/Kill` → 415 (存在, 方法/Content-Type 不匹配)
- 其余 23 个候选路径 (health/snapshot/exec/fs/host/vm/agent/metrics/config) → 全 404
- **无其他服务方法, 无更高权限攻击面**

### 影响评估
- 沙箱内任意命令 (uid 1000) — 与 cmd API 能力重叠, 但绕过 API 层 (审计/限制)
- 控制通道 MITM: 可伪造 SpawnEvent 响应给 celld (v207 实证 REPLAY-mod 被接受)
- **按 #3955363 先例 (ptrace patch 签名校验 → 全 CapEff + setuid(0) → N/A): 本链 (纯协议重放)
  影响相同 (own microVM), 攻击面 (sandbox-init 控制面/签名) 已在 Known findings → N/A**
- 技术价值: 即使官方修复 ptrace 面 (Yama), 本协议级重放仍然有效 — 修复需签名覆盖 body + 防重放

## 发现 2: CreateSnapshot 控制面无鉴权 + 任意 driveId/bucketBaseUrl (v192-v196, v215-v217)

### 事实
- 沙箱普通进程可连 `127.0.0.1:23456` (宿主 ControllerService, 端口注入沙箱 loopback;
  v215: 沙箱内 ss/proc 无此监听 → 宿主服务转发)
- `vercel.sandbox.api.controller.v1.ControllerService/CreateSnapshot` 无鉴权:
  - `driveId='sandbox'` / 任意非空值 (v216: 'nonexistent-zzz-216' 也触发) → 宿主真实快照
    (snap_xxx ID 生成) + 沙箱 stopped
  - `driveId=''` → 400 "drive_id is required" (唯一校验)
  - `bucketBaseUrl` 任意: s3://v1.vercel.com / s3://nonexistent.invalid / s3://127.0.0.1:23456 /
    s3://公网 S3 域名 全部接受 (v196)
- **无跨沙箱 IDOR** (v217): driveId=受害者沙箱 sid → 受害者 running 不受影响, 快照始终作用于
  当前沙箱自己
- 上传捕获失败 (v194/v217): 沙箱内 18081 listener 收不到上传 → 上传在宿主侧 loopback/
  沙箱 stopped 后发生 → SigV4 凭据捕获不可行 (无公网端点)
- 沙箱 stopped 后可 `GET /v2/sandboxes/{name}?resume=true` 恢复 (v216 实证), 数据可回读

### 影响评估
- DoS 自己 (快照 stop 沙箱) + 触发宿主快照存储消耗 — own microVM 范畴
- 数据外传方向 (bucketBaseUrl 任意) 未获上传实证; 即使外传也是自己的沙箱数据
- **与 #3954985/#3965216 (vda/快照原语) 同范畴, 无新影响 → N/A**

## 窗口总结 (2026-08-18 ~ 09-01)
- 共提交 6 份报告: 全部 N/A/dup (#3954985 自撤, #3955363 N/A, #3965216 N/A, #3972961 N/A,
  VPC dup, pidfd 自评 N/A)
- 合格标准 (EC2 host 新逃逸 / 跨租户 / firewall bypass+凭据 exfil / 新 host 写原语) 无突破
- 本会话 (v205-v217) 新增两个技术发现 (签名重放链 + CreateSnapshot 控制面), 均 own microVM 范畴

## 证据文件索引
- v205: `vda205_probe_user.py` (init.sock MITM 捕获 6 签名) + `_run_v205.py`
- v206/v207: 透明代理 + chunked/gzip 解析 + REPLAY-raw/mod
- v208: `vda208_probe_user.py` (重放矩阵 A/B/C/D 决定性) + `_run_v208.py`
- v209: 跨沙箱重放失败 + `_run_v209.py`
- v210: `vda210_probe_user.py` (60s/120s 延迟重放) + `_run_v210.py`
- v211/v212/v213: 服务枚举 (bug: classify bytes/str 类型; 先 hook 后探测时序) + `_run_v213.py`
- v215/v216/v217: driveId 变体 + 双沙箱 IDOR + resume + 上传捕获 + `_run_v215/216/217.py`
- 证据文件: /tmp/v208_a, /tmp/v208_id, /tmp/v210_60, /tmp/v210_120, /tmp/v213_ctrl (已随沙箱清理)

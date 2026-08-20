# Vercel Sandbox 逃逸报告归档（等待 triage）

## 报告信息

- **提交日期**：2026-08-20
- **标题**：Vercel Sandbox escape: user code can read/write the host rootfs block device /dev/vda
- **严重度**：CRITICAL（预检确认 CVSS 9.3）
- **弱点**：CWE-653 Improper Isolation or Compartmentalization
- **状态**：已提交，等待 H1 triage（资产由人工分配，Asset: Vercel sandbox (OTHER)）
- **报告链接**：（待用户补充）

## 漏洞核心

沙箱 /dev 暴露宿主 rootfs 块设备 /dev/vda（254:0），沙箱自身 rootfs 是 /dev/vdb（254:16）。沙箱内 root 进程可 O_RDWR 读写宿主盘（写 512B → fsync → 读回一致，非 COW 假写，已无痕还原）。

**判据实锤**（三证据）：
1. 设备号：vda 254:0（宿主）/ vdb 254:16（沙箱）
2. mountinfo：宿主 bind-mount 源全部来自 254:0（/etc/hosts、/etc/resolv.conf、/volumes/run/vercel/share、/run/cell/ca-cert.pem）
3. 沙箱内 /run/cell、/volumes、/opt/vercel 全部 NOT FOUND（只通过裸设备可达）

## 证据文件

| 文件 | 内容 |
|---|---|
| H1-vercel-sandbox-host-disk-access.md | 提交用精简报告（英文） |
| exp_j36_out.txt | 设备号对比 + mountinfo + 沙箱内不可见性 + vda 特征搜索（英文标签版，与原始输出逐字节一致） |
| exp_j37b_out.txt | 写测试完整证据链：O_RDWR → write 512 → fsync → READBACK True → RESTORE True |

## 实验脚本（保留在项目根目录）

- exp_j36.py — vda 身份验证
- exp_j37.py / exp_j37b.py — 写能力测试（j37 首版 pattern 长度 bug 误报 WRITE_IGNORED，j37b 修正）

## 相关实验链（J 系列，根目录）

exp_j26（0.1GB 首扫）→ exp_j30（0-100MB PAT 重扫）→ exp_j31/31b/31c（ext4→XFS 大端识别）→ exp_j32/33/34/35（inode 1042-1044 解析，celld.toml/xkernel.toml 定位，data fork 前 16B 动态混淆未破）

## 未解决线索（备用弹药，triage 要求补充时用）

- vda 上 ca-key.pem（vercel-proxy-ca 私钥）未找到 —— 找到可升证据强度
- celld.toml/xkernel.toml 内容被动态混淆（inode 1043/1044 data fork 前 16B 每次沙箱不同）
- /opt/vercel/celld-init.sh 的文件级定位（宿主 RCE 链理论可行，未实测）

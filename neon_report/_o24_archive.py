# -*- coding: utf-8 -*-
"""追加 §9(UTF-8 安全)到 Neon-Auth与DataAPI技术面-20260904.md"""
import io

content = """

---

## 9. org 角色越权 + Neon Functions Beta 面（_o1~_o23，2026-09-04）——均闭合

### 9.1 org member 越权矩阵——闭合
- 环境：na2(owner) + secn12(member)；org 数据**不在项目 PG**（neon_auth.member/organization/invitation 0 行——独立存储；user/session 在项目 PG）
- 端点×角色矩阵：invite-member/update-org/delete-org → member 403（YOU_ARE_NOT_ALLOWED_TO_*，服务端角色校验到位）；member 专属端点全集 404（只暴露最小端点集）
- **member 自提权（精确 memberId）→ 403 YOU_ARE_NOT_ALLOWED_TO_UPDATE_THIS_MEMBER**（member 行 id 从 accept-invitation 响应可得，id=UUIDv4 独立于 userId）；member 可正常 leave-org
- 参数变体矩阵（memberIdOrEmail/userId/email/memberId）→ 全部 400/403；slug 语义：update-member-role/remove-member 需精确 memberId
- ★ 教训：owner 基线调用 delete-org 真的删掉了测试 org（_o1 自毁）——owner 对照必须只用可逆操作
- **结论：Better Auth organization 角色模型服务端校验完整，无越权**

### 9.2 Functions 控制面（OpenAPI Functions tag 8 端点 + 部署链）——闭合
- 端点状态：GET functions list 200（Beta 在 staging 启用）；不存在 slug → 404 "function not visible on branch"（无信息泄露）；PATCH/DELETE 无 CSRF → 403（Gorilla）；slug regex 严格（小写 DNS label，大写/下划线/连字符边界/超长 → 400）
- **无 POST /functions 创建端点——POST /functions/{slug}/deployments 隐式创建**（multipart: zip + runtime=nodejs24 + environment JSON 字符串）
- zip 格式确认：zip 根 index.js（ESM default export {fetch}）+ package.json {type:module} → 4s 内 completed
- env 语义验证：deployment 响应/GET function 只回显 env **names**（值 write-only ✓）；空值 env 被剔除（= 删除语义）
- zip 异常矩阵：postinstall 脚本 → completed（**构建器无 npm install**）；zip slip（../路径）→ failed `mksquashfs build failed (HTTP 422): bad_path`（**构建管线：zip → squashfs**）；20MB zip 201 接受；无 index.js 也 completed（构建不校验 handler）
- custom-domains：A 项目 404 "custom domains not available for this project"（项目级 flag 关闭）；list 端点同 404
- 部署清理：所有测试函数已 DELETE（204）

### 9.3 ★ Functions 运行时隔离探测（module-scope 自执行 + console.log→Logs API 闭环）——隔离良好
- **部署后平台自动 invoke**（invoke begin/end 日志）→ module-scope 代码必然执行 → 探测函数方案可行（无需公网入口）
- 运行时画像：nodejs24 容器 + squashfs 挂载；eth0=192.168.221.x/31（点对点 veth，/31 对端=宿主侧）；内存 2048MiB
- env 注入（全部 branch-scoped 设计内）：DATABASE_URL(+UNPOOLED)/PGHOST/PGPASSWORD；AWS_ACCESS_KEY_ID=nak_live_*/SECRET=nsk_live_*/AWS_ENDPOINT_URL_S3=br-<bid>.storage.c-1…（对象存储凭据，**每次部署轮换**）；NEON_AI_GATEWAY_TOKEN=TELEMETRY_TOKEN=nt_live_*（同值）；NEON_AUTH_JWKS_URL/BASE_URL；NEON_DATA_API_URL；NEON_LOAD_PORT=8082/DATA_PORT=8081/MOUNT_POINT=/opt/function（本地 sidecar）
- **网络隔离验证**：
  - IMDS 169.254.169.254 / 100.100.100.200 → 全超时（隔离 ✓）
  - 对端 192.168.221.14 全端口拒绝；同段 .0-.30 无响应（无邻居暴露 ✓）
  - 出公网正常（ipify 200）；otel.c-1 内部域可达（https 464 自定义响应——公网 IP 18.119.245.208）
  - **无内部 DNS 视图**：*.c-1.us-east-2.aws.neon.build 全 wildcard 解析到同一组公网 IP（3.22.12.41/3.14.183.206/3.148.58.16——除 otel/ai/storage/独立记录外），函数内=外部一致，零 RFC1918
- 本地 sidecar：8081 DATA → catch-all 200 "ok"（任意路径/方法）；8082 LOAD → JSON 路由 API（60+ 路径字典全 404 {"code":"not_found"}——未命中，无可利用端点）
- **结论：Functions 运行时隔离实现良好（容器+点对点网络+egress 白名单+IMDS 隔离+无内部 DNS）；控制面实现安全。invocation_url 公网调用 → ALB 403（staging 边缘封锁，生产行为不可外推）。无洞**

### 9.4 环境残留更新
- org sec-n12-org / sec-o6-org / sec-o7-org 已全部删除（owner delete 200）；测试函数全清理（204）
- 无新增残留

### 9.5 结论
- org 越权面 + Functions 面（控制面+运行时）全部闭合；无新报告候选
- Functions Beta 值得在**生产**（console.neon.tech）复查 invocation 面（staging ALB 封锁不可测）；custom-domains 面需功能开放项目
"""

with io.open(r'D:/scan/neon_report/Neon-Auth与DataAPI技术面-20260904.md', 'a', encoding='utf-8') as f:
    f.write(content)
print('appended', len(content), 'chars')

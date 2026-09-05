# -*- coding: utf-8 -*-
content = '''

## 12. 表名泄露利用链追查（V25~V26，2026-09-05）——顺藤摸瓜到 jwks 私钥，链断于 KMS 信封加密

### 12.1 project_config 定位（V25）——纯配置镜像，无敏感
- /postgres/auth/* 500 泄露的表 = neon_auth.project_config（仅 1 行）：列 = trusted_origins/social_providers/email_provider/email_and_password/allow_localhost/plugin_configs/webhook_config
- 内容 = 控制面 auth 配置的 DB 镜像（与 6.1 API 画像一致）→ 无密钥字段 → 泄露面 = 配置值（API 已可读）+ 表名（内部 schema 结构线索）
- 库名 SQL 字符探针（引号/分号/注释/%27/%00/反斜杠 等 13 种）→ 全 404/400（参数化查询，无注入）；template0 → 500 连接超时、template1 → 同 project_config 500（库存在性 oracle 仅限自己 endpoint → 无跨租户）

### 12.2 neon_auth.jwks 表：Data API JWT 私钥落库（V26）——链断于信封加密
- 表结构：id/publicKey/privateKey/createdAt/expiresAt；1 行，publicKey = Ed25519 JWK
- 决定性关联：真实 /token JWT 的 header kid=6ab964bf... = jwks 表 id；用存储 publicKey 验签真实 JWT → VALID（该 keypair 就是 Data API JWT 签名者）
- privateKey 列：JSON 编码的 338-hex 字符串（169 bytes 随机二进制）→ 解析全失败：前/后/滑窗全 32B seed 窗口派生公钥均不匹配、DER 载入失败、非双层 hex → KMS 信封加密密文（明文私钥在 Neon 服务端）
- 权限矩阵：新建低权限 role（LOGIN+CONNECT+USAGE）→ SELECT neon_auth 全 9 表 → 全 DENY（schema 表权限仅授 owner）→ 跨主体无门；owner 读到的只是密文 → 伪造链断
- 结论：私钥加密落库是 Neon 安全设计（可恢复性/多区域），DB owner 无法提取明文 → 无 JWT 伪造；测试 role 已 REVOKE+DROP
- 补充观察（Informational）：Data API 签名私钥密文存在于用户 DB——若未来 KEK 管理失当或加解密端点出现，此面需重审；当前无利用路径
'''
with open(r'F:\scan\neon_report\Neon-Auth与DataAPI技术面-20260904.md', 'a', encoding='utf-8') as f:
    f.write(content)
print('ok')

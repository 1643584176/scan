# Figma Community 服务 — 会话进度存档 (2026-09-08 暂存)

> **STATUS: 暂停** (2026-09-08 用户决定暂停 Figma,以下为恢复所需全部状态)
> 恢复起点:p111+ 脚本即插即用;关键卡点:B 账号 community 写面被 anti-abuse 限制(需用户 UI 确认/等待恢复)

---

## 一、账号与凭据

| 账号 | UID | Community Profile ID | handle/显示名 | 凭据文件 | 状态 |
|---|---|---|---|---|---|
| A = 1643 (1643584176@qq.com) | 1666382703778278399 | 1678723815222325641 | pccp / pccp | `_p103_curl_A.txt`(bash 格式,单 A token) | ✅ 写面正常 |
| B = 7294 (729488839@qq.com) | 1667396392129259941 | 1667396392225089633 | pccp_b2_9fmvxl / boboa | `_p102_curl.txt`(PowerShell 格式,双 token) | ⚠️ **写面被限**(见下) |

- A 的 TEAM: 1666382706663462213;B 的 TEAM: 1667396394890946753
- 第三方资源:free-icon-pack = 内部 UUID `d2b50308-9c96-4681-b23b-0130308047ee` ↔ hub 数字 id `886554014393250663`(owner Leonid,profile id **1891080**,primary UID 735205186788041733,312 followers);GWP TFT = hub `871334426251486294`

## 二、⚠️ B 账号 anti-abuse 限制(最重要卡点)

- **现象**(~04:10 起):B 身份所有 community 写操作失败——POST/DELETE 评论 → `400 must_have_public_profile`;PUT /api/follows → 404;GET(评论列表/user state)正常;`user state` 里 `community_blocked_at=null`
- **时间点**:p106-p110 期间 30 分钟内 8+ 评论+删除循环测试之后 → 高度怀疑高频测试触发 Figma anti-abuse,把 B profile 置为非公开
- **A 身份同操作全正常**(对照实验确认非端点问题)
- **待办**(需用户):切 B 浏览器看 `https://www.figma.com/@pccp_b2_9fmvxl` profile 页状态(警告条/需重新公开?);或等自动恢复(时长未知)
- **残留**:B 的 HTML 测试评论 `1679002090451472172` 留在 Leonid 资源上删不掉(B 写面恢复后可 `DELETE /api/community_comments/1679002090451472172`)
- **教训**:评论写测试降频(≥30s 间隔),避免删除循环

## 三、候选发现(未定稿未提交)

### 候选 1:无头像用户 email MD5 泄露(gravatar)——证据链完整,待评估
- 机制:`author/publisher/follower` 对象的 `img_url` 对无头像用户返回 `https://www.gravatar.com/avatar/{md5}?size=...`——**hash = 注册邮箱的 MD5**(双账号精确验证:`md5(1643584176@qq.com)=2f908873db5bed216938407d7d95fde7` ✓、`md5(729488839@qq.com)=4eca913924df2d3229ae6a841d9352c2` ✓)
- 公开入口(任意登录用户,无额外权限):
  - `GET /api/resources/{uuid}/comments`(评论作者;p107:11 作者 4 个 gravatar)
  - `GET /api/followers/{profile_id}` / `GET /api/following/{profile_id}`(30/页可翻页;p122:Leonid 首页 30 人 10 个 hash)
  - 资源详情 publisher/creator(无头像时)
- 攻击价值:email 验证(撞库匹配)、跨平台身份关联(gravatar 是全局 email 指纹)、与 handle/实名绑定 → 匿名性破坏
- 影响面:全站未设置头像的 Community 用户
- 证据文件:`_p122_followers_Leonid.json`、`_p122_followers_Kryston.json`、`_p107_comments_list.json`、`_p106_commentB_full.json`
- 评估:低-中危(CWE-200);风险:Figma 可能辩称 gravatar 是老设计/头像 URL 非 PII → 可能 N/A/low

## 四、端点考古成果(bundle _js/ 提取,本会话新确认)

### 已实测可用
- `GET /api/resources/{uuid}/comments` — 评论列表(登录必须;未登录 403);参数 `page_size`(注意返回数不稳定:page_size=5 时返回 4/3/0/4/5 乱序,cursor 分页在 `pagination.next_page`);总数 21 条(UI 显示 43+ 未解,可能含回复)
- `POST /api/community_comments` body `{message_meta:[{t}], resource_id: hub_id, resource_type: "hub_file"}` — 发评论(需 public profile)
- `PUT/DELETE /api/community_comments/{id}` body `{message_meta:[{t}]}` — 改/删;非作者 → 403 "You must be the author";额外字段白名单忽略(p108 注入证伪);删除硬删(重放 404)
- `POST /api/profile/{blocked_profile_id}/block` body `{block_type:"restrict", profile_id: 自己PID}` — **restrict 用户**;`DELETE` 同 URL = unrestrict(可逆);语义 = 对方不能在自己资源上评论+自己视角隐藏对方评论;UI 有 getRestrictedProfiles 列表
- `PUT /api/follows` body `{followed_profile_id}` / `DELETE` 同 — follow/unfollow(200 即时, follower_count +1);**POST 全 404(此前黑盒猜错)**
- `GET /api/followers/{profile_id}` / `GET /api/following/{profile_id}` — 30/页,返回完整 profile 对象(含 img_url/realtime_token);**Leonid profile id = 1891080**(短 id!creator.id 735205186788041733 是 primary UID 不是 profile id——p120 用错导致空列表)
- `GET /api/user/state?fuid={uid}` — fuid 参数被忽略恒返回自己(交叉读取证伪);含 user.handle/img_url(自己 gravatar)
- `POST /api/community_comments/{id}/report` — 举报;admin 带 `{hide:true}` 可隐藏(普通用户无参数,仅计数)
- `POST /api/profile/merge` {primary_user_id, secondary_user_id}、`POST /api/profile/generate_handle`、`POST /api/profile`(upsert)— **已有报告 N/A 覆盖,勿重复**

### 已证伪面(勿重试)
- 评论 PUT 注入 resolved_at/hidden_at/parent_id 等 → 全部忽略(白名单)
- save 端点 savedByOrgId/includePrivateResources → 参数忽略恒返回自己列表
- /api/profile/{id} GET 详情 → 404(非详情端点)
- 评论 HTML 注入 → **存储原样未转义但渲染纯文本**(用户 UI 确认 <b>/<a> 不渲染、链接不可点)= XSS 面关闭
- 评论读取 detail 端点(11 变体全 404);未登录 API → 403(WAF,需浏览器)

## 五、已提交报告(勿重复这些面)
- H1-community-profile-primary-user-idor.md — **N/A 终判**(primary_user/merge owner 校验存在,干净状态不可复现)
- H1-community-profile-forced-merge-takeover.md(同源,已结)
- H1-plan-leak.md、H1-published-package-missing-authz.md、H1-private-make-source-code-authz-chain.md、H1-F2-private-make-source-short.md(其他面,已结)

## 六、挂起待测链(需用户配合恢复)
1. **A 发布文件到 Community**(用户 A 浏览器 Share → Publish,给资源页 URL → related_content 拿 UUID)→ creator 回复链:A(creator)回复自己资源 B 的评论基线 / A 回复第三方资源评论的 creator 校验 / 评论读取端点读私有资源
2. **restrict 效果链**:A restrict B → B 用 API 评论 A 资源 → 200=restrict 绕过(服务端不 enforce)／403=正常(需 B 写面恢复)
3. **B 写面恢复确认**(用户 B 浏览器看 profile 状态)
4. followers 全量翻页拉取(放大 gravatar 泄露影响面,报告用)

## 七、脚本索引(恢复即用)
- `_figma_p110_clean.py` 清理+pagination 探测 / `_figma_p112_tri.py` md5 验证+state+翻页 / `_figma_p113_anon.py` 未登录面 / `_figma_p114_statex.py` fuid 交叉(证伪)/ `_figma_p115_bstate.py` B 写面确认 / `_figma_p120_newapi.py`+`_figma_p121_fix.py`+`_figma_p122_follow2.py` follow/followers 闭环 / `_figma_p116_authors.py` 头像分布 / `_figma_p117_surface.py` 泄露面制图 / `_figma_p118_apiscan.py`+`_figma_p123_blockarch.py`+`_figma_p124_unblock.py`+`_figma_p125_t9.py`+`_figma_p126_blockmain.py` bundle 考古
- 双格式 header 解析 load_headers 兼容 bash `-H 'k: v'` 与 PowerShell `-H ^"k: v^"`(cookie 剥 ^)——各脚本顶部可复用

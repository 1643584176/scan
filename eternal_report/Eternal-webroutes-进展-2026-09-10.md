# Eternal webroutes 进展（2026-09-10）

## 一、端点表挖掘（z_main JS → 154 端点）
- 数据源：zwstatic.zomato.com/z_main-8efa4cf644fa76389041.js（394KB，搜索页主 bundle）
- 提取：/webroutes/*（~120）、/webapi/*、/gw/* 全表（见 _et59 提取输出）
- **新主机发现：external.zomans.com**（JS 常量 `$e`）
- 关键真实端点：/webapi/searchapi.php、/webroutes/search/autoSuggest、search/home、search/applyFilter、location/search、locationGeoData

## 二、无会话可达性判别（40 个查询类端点）
### A. 免登录可达·等参数（400 "error"）——重点候选
- /webroutes/restaurant/info —— 参数 res_id ✅（200）
- /webroutes/reviews/loadMore —— 参数 res_id ✅（200）
- /webroutes/menu/viewMenu —— 参数 res_id ✅（200）
- 同族待测：reviews/sortReviews、reviews/comment/loadMore、photos/loadMore、photos/viewGallery、restaurant/getHygieneDetails、restaurant/getHyperpureDetails
### B. 免登录·200 直接可用
- location/search、location/get、kitchen/city（全城市 ID 表）、feeding/getTotalAmount、home/quickLinks、home/o2quickLinks、getPage、ads、blog/posts、order/details、promo/info
### C. 要登录（跳过）
- reviews/suggestTags（401 "Please login"）、dote/address、loyaltyqrscan/getResList
### D. POST-only
- restaurant/userModalInfo、cdng/*（5 个）、hygiene、dote/home、dote/cart、postOrder/pollCrystalData

## 三、参数名确认（ET60）
- res_id=1/3 → 200 ✅
- resId / restaurant_id / id → 400 ❌
- 唯一正确参数名 = **res_id**（与历史报告 #838855 "LocalParams (res_id)" 同名同源，但端点为新一代 webroutes 体系）

## 四、res_id 探测与 Akamai 行为记录（ET61-63）
| 请求 | 结果 |
|---|---|
| res_id=3（基线） | 200，11KB JSON |
| **res_id=3'（单引号）** | **500 len=0（第一发——过了 WAF 打到应用层）** |
| res_id=3'（复测第二轮） | 403 Akamai（自适应已升级） |
| res_id=3 and 1=1 / and 1=2 / 0 / 99999999 / 3.5 | 403 Akamai |
| res_id=-1 | 200 {"message":"error"}（应用接受纯数值） |
| 引号族/tab/空格/hash（第二轮） | 全 403 |
| 冷却 60s 后正常 res_id=3 | **403（IP 级临时封禁生效）** |

### 结论
1. 该面防护 = **Akamai 自适应 WAF**；短窗口恶意变体 >~5 发 → 升级为 IP 级封禁（连正常请求）。
2. **单引号首发得到 500（非 403）** = 该发穿过了 WAF 并让应用崩——**信号未判别**（SQL 语法错 or 应用解析错）。
3. Akamai 规则命中集：单引号、空格+and、%09、%20 尾随、hash 等（第二轮起全拦）。

## 五、下一步计划
1. **冷却**：停止一切 www.zomato.com 请求（IP 已被临时封禁，等自然解封）。
2. 解封后**完美数据探测**：只用"纯数字畸形"（前导零 0003 / 超长数字 / 科学计数 3e0 / 边界大数 / 全角数字），**单发、间隔 ≥15s、每轮 ≤5 发**，观察响应差异（200/500/长度变化）。
3. 其他面：winecellar.zomato.com（Tier1 冷面）、external.zomans.com——注意集团级 Akamai 可能共享封禁。
4. 引号族已触发规则，冷却期后也避免直发；需变体（编码/形态）且极低频。

## 六、本轮资产清单（脚本）
- _et45 route probe / _et47 dbsvc2 / _et49 baas scan / _et50 portmatrix
- _et51-53 search JS 挖掘 / _et54-56 端点探活
- _et57 chunks 下载（18 个 zc_*.js）/ _et58 错误消息探路
- _et59/59b 端点表+可达性判别 / _et60 参数名矩阵
- _et61 res_id 探测 / _et62 引号差分 / _et63 冷却验证

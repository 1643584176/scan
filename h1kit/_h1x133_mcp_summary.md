# H1 前端源码审计进展 (2026-09-09)

## 本轮新发现:Agentic UI MCP 面(HAI AI 助手的新渲染架构)

### 链路(源码还原)
1. AI artifact payload 带 `renderer_uri`(默认 `ui://prefab/app`,NGe 常量)
2. 前端宿主 cG(AgenticUiMcpArtifact)若 flag `AGENTIC_UI_MCP` 开启(org 级):
   - 主 iframe src = `/hai/agentic_ui_mcp/sandbox?contentType=rawhtml`(v = new URL(MGe, origin))
   - 读资源:POST `/hai/agentic_ui_mcp/resources/read` {uri, organization_id} → {content, mimeType}(sG;uri==renderer_uri 走 sessionStorage 缓存 RGe)
   - sandbox iframe 通过 postMessage 协议通信(ui/notifications/sandbox-resource-ready 等)
3. sandbox 页面(匿名 200):`/hai/agentic_ui_mcp/sandbox`,带 data-parent-origin + data-allowed-img-sources(S3 附件域)
4. sandbox JS(1738B 可读,已下载 _h1x131_sandbox.js):
   - parent origin 校验(t.source===window.parent && t.origin===parentOrigin 才收)
   - inner iframe sandbox=`allow-scripts`(无 same-origin/forms/popups)
   - 渲染前注入 CSP:`default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; img-src data: blob: <S3>; font-src data:`
   - html 无 head 则包装;Blob URL 载入
   - child→parent 转发 postMessage 到 parentOrigin(hackerone.com)
5. vendor MCP SDK(协议 schema):
   - uri 必须 ui:// 前缀否则 throw(hRr)
   - CSP 域列表(connect/resource/frame/base-uri)与权限(camera/mic/geo/clipboard)由**资源元数据**声明,空=全禁(安全默认)
   - 可选 dedicated origin(domain 字段,供 OAuth/CORS)

### 安全评估
- 前端链严密:opaque origin + CSP none + img 仅 S3 白名单 + parent origin 校验 + ui:// scheme 强制
- contentType 参数后端完全忽略(变体全同页)
- resources/read **匿名 412 Precondition Failed**(端点存在,需登录态+CSRF 才可测)
- 真正的校验点 = 后端 resources/read 的 uri 解析(ui:// 注册表?是否有 file/http 代理=SSRF?)——黑盒待测

### 其它端点清单(64 个,见 _h1x124_endpoints.txt)
- /hackbot/genii GET {report_id}(Genius 组件,任意 report_id 触发分析)
- /reports/{id}/export/raw POST {include_internal_activities, redact_usernames}(include_internal_activities=true → 内部活动导出?)
- /reports/{id}/export/zip POST {authenticity_token}
- /hai/agentic_ui_mcp/resources/read(上)
- /reports/bulk、/reports/{db_id}/public_view、/settings/deactivate 等(传统 Rails 端点)

## 待登录态测试点(按价值排序)
1. **MCP resources/read uri 变体矩阵**(SSRF/任意读候选,技术层):
   ui://prefab/app(基线)、ui://x、ui://prefab/../x、file:///etc/passwd、
   http://127.0.0.1/、http://169.254.169.254/、https://attacker.com/、gopher://
   观察:错误差异(oracle)/是否代理读
2. me{has_api_token} + updateUserApiToken → api.hackerone.com 通道
3. hackbot/genii report_id 越权(他人报告触发?)
4. export/raw include_internal_activities=true(他人/自己 closed)

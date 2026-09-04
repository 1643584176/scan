# Netlify 接口清单(OpenAPI 公开 + bundle 内部)

> 来源:swagger.yml v2.57.1 + app.netlify.com bundle v4 静态分析
> 参数列:R=必传 O=可选;caller=调用 bundle;query=URL 查询参数;fn=最近函数

## A. 公开 API(OpenAPI, 180 条)

| 方法 | 路径 | 参数(名:R/O) | 说明 |
|---|---|---|---|
| DELETE | `/accounts/{account_id}` | - |  |
| DELETE | `/accounts/{account_id}/env/{key}` | account_id:R,key:R,site_id:O |  |
| DELETE | `/accounts/{account_id}/env/{key}/value/{id}` | account_id:R,id:R,key:R,site_id:O |  |
| DELETE | `/agent_runners/{agent_runner_id}` | - |  |
| DELETE | `/agent_runners/{agent_runner_id}/sessions/{agent_runner_session_id}` | - |  |
| DELETE | `/deploy_keys/{key_id}` | - |  |
| DELETE | `/deploys/{deploy_id}` | deploy_id:R |  |
| DELETE | `/dns_zones/{zone_id}` | - |  |
| DELETE | `/dns_zones/{zone_id}/dns_records/{dns_record_id}` | - |  |
| DELETE | `/hooks/{hook_id}` | - |  |
| DELETE | `/sites/{site_id}` | - |  |
| DELETE | `/sites/{site_id}/agent_runner_hooks/{id}` | - |  |
| DELETE | `/sites/{site_id}/assets/{asset_id}` | - |  |
| DELETE | `/sites/{site_id}/build_hooks/{id}` | - |  |
| DELETE | `/sites/{site_id}/database` | - |  |
| DELETE | `/sites/{site_id}/database/branch/{branch_id}` | - |  |
| DELETE | `/sites/{site_id}/database/compute/settings` | - |  |
| DELETE | `/sites/{site_id}/database/snapshot/{snapshot_id}` | - |  |
| DELETE | `/sites/{site_id}/deploys/{deploy_id}` | deploy_id:R,site_id:R |  |
| DELETE | `/sites/{site_id}/dev_server_hooks/{id}` | - |  |
| DELETE | `/sites/{site_id}/dev_servers` | branch:O |  |
| DELETE | `/sites/{site_id}/forms/{form_id}` | site_id:R,form_id:R |  |
| DELETE | `/sites/{site_id}/services/{addon}/instances/{instance_id}` | - |  |
| DELETE | `/sites/{site_id}/snippets/{snippet_id}` | - |  |
| DELETE | `/submissions/{submission_id}` | - |  |
| DELETE | `/{account_slug}/members/{member_id}` | - |  |
| GET | `/accounts` | minimal:O |  |
| GET | `/accounts/types` | - |  |
| GET | `/accounts/{account_id}` | - |  |
| GET | `/accounts/{account_id}/ai-gateway/token` | - |  |
| GET | `/accounts/{account_id}/audit` | query:O,log_type:O,None:O,None:O |  |
| GET | `/accounts/{account_id}/env` | account_id:R,context_name:O,scope:O,site_id:O |  |
| GET | `/accounts/{account_id}/env/{key}` | account_id:R,key:R,site_id:O |  |
| GET | `/agent_runners` | account_id:R,site_id:R,None:O,None:O,state:O,title:O,branch:O,result_branch:O,from:O,to:O |  |
| GET | `/agent_runners/{agent_runner_id}` | - |  |
| GET | `/agent_runners/{agent_runner_id}/sessions` | None:O,None:O,state:O,from:O,to:O,order_by:O |  |
| GET | `/agent_runners/{agent_runner_id}/sessions/{agent_runner_session_id}` | - |  |
| GET | `/ai-gateway/providers` | - |  |
| GET | `/api/v1/sites/{site_id}/env` | context_name:O,scope:O,site_id:R |  |
| GET | `/billing/payment_methods` | - |  |
| GET | `/builds/{build_id}` | - |  |
| GET | `/deploy_keys` | - |  |
| GET | `/deploy_keys/{key_id}` | - |  |
| GET | `/deploys/{deploy_id}` | deploy_id:R |  |
| GET | `/dns_zones` | account_slug:O |  |
| GET | `/dns_zones/{zone_id}` | - |  |
| GET | `/dns_zones/{zone_id}/dns_records` | - |  |
| GET | `/dns_zones/{zone_id}/dns_records/{dns_record_id}` | - |  |
| GET | `/forms/{form_id}/submissions` | form_id:R,None:O,None:O |  |
| GET | `/hooks` | site_id:R |  |
| GET | `/hooks/types` | - |  |
| GET | `/hooks/{hook_id}` | - |  |
| GET | `/oauth/tickets/{ticket_id}` | ticket_id:R |  |
| GET | `/services/` | - |  |
| GET | `/services/{addonName}` | - |  |
| GET | `/services/{addonName}/manifest` | - |  |
| GET | `/sites` | name:O,filter:O,None:O,None:O |  |
| GET | `/sites/{site_id}` | feature_flags:O |  |
| GET | `/sites/{site_id}/agent_runner_hooks` | - |  |
| GET | `/sites/{site_id}/agent_runner_hooks/{id}` | - |  |
| GET | `/sites/{site_id}/ai-gateway/token` | - |  |
| GET | `/sites/{site_id}/assets` | - |  |
| GET | `/sites/{site_id}/assets/{asset_id}` | - |  |
| GET | `/sites/{site_id}/assets/{asset_id}/public_signature` | - |  |
| GET | `/sites/{site_id}/build_hooks` | - |  |
| GET | `/sites/{site_id}/build_hooks/{id}` | - |  |
| GET | `/sites/{site_id}/builds` | None:O,None:O |  |
| GET | `/sites/{site_id}/database` | role:O |  |
| GET | `/sites/{site_id}/database/branch/{branch_id}` | role:O |  |
| GET | `/sites/{site_id}/database/branches` | - |  |
| GET | `/sites/{site_id}/database/compute/settings` | - |  |
| GET | `/sites/{site_id}/database/migrations` | branch:O |  |
| GET | `/sites/{site_id}/database/migrations/{name}` | branch:O |  |
| GET | `/sites/{site_id}/database/snapshots` | - |  |
| GET | `/sites/{site_id}/deployed-branches` | - |  |
| GET | `/sites/{site_id}/deploys` | None:O,None:O |  |
| GET | `/sites/{site_id}/deploys/{deploy_id}` | site_id:R,deploy_id:R |  |
| GET | `/sites/{site_id}/dev_server_hooks` | - |  |
| GET | `/sites/{site_id}/dev_server_hooks/{id}` | - |  |
| GET | `/sites/{site_id}/dev_servers` | None:O,None:O |  |
| GET | `/sites/{site_id}/dev_servers/{dev_server_id}` | - |  |
| GET | `/sites/{site_id}/dns` | - |  |
| GET | `/sites/{site_id}/files` | site_id:R |  |
| GET | `/sites/{site_id}/files/{file_path}` | site_id:R,file_path:R |  |
| GET | `/sites/{site_id}/forms` | site_id:R |  |
| GET | `/sites/{site_id}/functions` | site_id:R,filter:O |  |
| GET | `/sites/{site_id}/metadata` | - |  |
| GET | `/sites/{site_id}/plugin_runs/latest` | site_id:R,packages:R,state:O |  |
| GET | `/sites/{site_id}/service-instances` | - |  |
| GET | `/sites/{site_id}/services/{addon}/instances/{instance_id}` | - |  |
| GET | `/sites/{site_id}/snippets` | - |  |
| GET | `/sites/{site_id}/snippets/{snippet_id}` | - |  |
| GET | `/sites/{site_id}/ssl` | site_id:R |  |
| GET | `/sites/{site_id}/ssl/certificates` | site_id:R,domain:R |  |
| GET | `/sites/{site_id}/submissions` | site_id:R,None:O,None:O |  |
| GET | `/sites/{site_id}/traffic_splits` | - |  |
| GET | `/sites/{site_id}/traffic_splits/{split_test_id}` | - |  |
| GET | `/submissions/{submission_id}` | query:O,None:O,None:O |  |
| GET | `/user` | - |  |
| GET | `/{account_id}/builds/status` | - |  |
| GET | `/{account_slug}/members` | - |  |
| GET | `/{account_slug}/members/{member_id}` | - |  |
| GET | `/{account_slug}/sites` | name:O,account_slug:R,None:O,None:O |  |
| PATCH | `/accounts/{account_id}/env/{key}` | account_id:R,key:R,site_id:O,env_var:O |  |
| PATCH | `/agent_runners/{agent_runner_id}` | - |  |
| PATCH | `/agent_runners/{agent_runner_id}/sessions/{agent_runner_session_id}` | is_published:O |  |
| PATCH | `/deploys/{deploy_id}/validations_report` | deploy_id:R,report:R |  |
| PATCH | `/sites/{site_id}` | site:R |  |
| POST | `/accounts` | accountSetup:R |  |
| POST | `/accounts/{account_id}/env` | env_vars:O,account_id:R,site_id:O |  |
| POST | `/agent_runners` | site_id:R,deploy_id:O,branch:O,prompt:O,agent:O,model:O,parent_agent_runner_id:O,dev_server_image:O,file_keys:O |  |
| POST | `/agent_runners/upload_url` | account_id:R,filename:R,content_type:R |  |
| POST | `/agent_runners/{agent_runner_id}/archive` | - |  |
| POST | `/agent_runners/{agent_runner_id}/commit` | target_branch:R |  |
| POST | `/agent_runners/{agent_runner_id}/pull_request` | - |  |
| POST | `/agent_runners/{agent_runner_id}/sessions` | prompt:O,agent:O,model:O,file_keys:O |  |
| POST | `/builds/{build_id}/log` | - |  |
| POST | `/builds/{build_id}/start` | - |  |
| POST | `/deploy_keys` | - |  |
| POST | `/deploys/{deploy_id}/cancel` | deploy_id:R |  |
| POST | `/deploys/{deploy_id}/lock` | deploy_id:R |  |
| POST | `/deploys/{deploy_id}/plugin_runs` | deploy_id:R,plugin_run:O |  |
| POST | `/deploys/{deploy_id}/unlock` | deploy_id:R |  |
| POST | `/dns_zones` | DnsZoneParams:R |  |
| POST | `/dns_zones/{zone_id}/dns_records` | dns_record:R |  |
| POST | `/hooks` | site_id:R,hook:R |  |
| POST | `/hooks/{hook_id}/enable` | - |  |
| POST | `/oauth/tickets` | client_id:R,body:O |  |
| POST | `/oauth/tickets/{ticket_id}/exchange` | ticket_id:R |  |
| POST | `/purge` | payload:R |  |
| POST | `/sites` | site:R,configure_dns:O |  |
| POST | `/sites/{site_id}/agent_runner_hooks` | agentRunnerHook:R |  |
| POST | `/sites/{site_id}/assets` | name:R,size:R,content_type:R,visibility:O |  |
| POST | `/sites/{site_id}/build_hooks` | buildHook:R |  |
| POST | `/sites/{site_id}/builds` | branch:O,clear_cache:O,image:O,template_id:O,title:O,zip:O |  |
| POST | `/sites/{site_id}/database` | database:O |  |
| POST | `/sites/{site_id}/database/branch` | branch:R |  |
| POST | `/sites/{site_id}/database/branch/{branch_id}/reset` | force:O,role:O,reset:O |  |
| POST | `/sites/{site_id}/database/migrations/{deploy_id}` | migrations:O |  |
| POST | `/sites/{site_id}/database/snapshot` | snapshot:O |  |
| POST | `/sites/{site_id}/database/snapshot/{snapshot_id}/restore` | restore:O |  |
| POST | `/sites/{site_id}/deploys` | title:O,deploy:R |  |
| POST | `/sites/{site_id}/deploys/{deploy_id}/restore` | site_id:R,deploy_id:R |  |
| POST | `/sites/{site_id}/dev_server_hooks` | devServerHook:R |  |
| POST | `/sites/{site_id}/dev_servers` | branch:O |  |
| POST | `/sites/{site_id}/dev_servers/{dev_server_id}/activity` | - |  |
| POST | `/sites/{site_id}/dev_servers/{dev_server_id}/state` | body:R |  |
| POST | `/sites/{site_id}/services/{addon}/instances` | config:R |  |
| POST | `/sites/{site_id}/snippets` | snippet:R |  |
| POST | `/sites/{site_id}/ssl` | site_id:R,certificate:O,key:O,ca_certificates:O |  |
| POST | `/sites/{site_id}/traffic_splits` | branch_tests:R |  |
| POST | `/sites/{site_id}/traffic_splits/{split_test_id}/publish` | - |  |
| POST | `/sites/{site_id}/traffic_splits/{split_test_id}/unpublish` | - |  |
| POST | `/{account_slug}/members` | accountAddMemberSetup:R |  |
| POST | `/{account_slug}/sites` | site:O,configure_dns:O,account_slug:R |  |
| PUT | `/accounts/{account_id}` | accountUpdateSetup:O |  |
| PUT | `/accounts/{account_id}/env/{key}` | account_id:R,key:R,env_var:O,site_id:O |  |
| PUT | `/deploys/{deploy_id}/edge_functions/{code_sha}` | deploy_id:R,code_sha:R,file_body:R,None:O |  |
| PUT | `/deploys/{deploy_id}/files/{path}` | deploy_id:R,path:R,size:O,file_body:R |  |
| PUT | `/deploys/{deploy_id}/functions/{name}` | deploy_id:R,name:R,runtime:O,invocation_mode:O,timeout:O,size:O,file_body:R,None:O |  |
| PUT | `/dns_zones/{zone_id}/transfer` | - |  |
| PUT | `/hooks/{hook_id}` | hook:R |  |
| PUT | `/sites/{site_id}/agent_runner_hooks/{id}` | agentRunnerHook:R |  |
| PUT | `/sites/{site_id}/assets/{asset_id}` | state:R |  |
| PUT | `/sites/{site_id}/build_hooks/{id}` | buildHook:R |  |
| PUT | `/sites/{site_id}/database/branch/{branch_id}/compute/settings` | computeSettings:R |  |
| PUT | `/sites/{site_id}/database/compute/settings` | computeSettings:R |  |
| PUT | `/sites/{site_id}/deploys/{deploy_id}` | site_id:R,deploy_id:R,commit_ref:O,deploy:R |  |
| PUT | `/sites/{site_id}/dev_server_hooks/{id}` | devServerHook:R |  |
| PUT | `/sites/{site_id}/disable` | reason:R |  |
| PUT | `/sites/{site_id}/dns` | - |  |
| PUT | `/sites/{site_id}/enable` | - |  |
| PUT | `/sites/{site_id}/metadata` | metadata:R |  |
| PUT | `/sites/{site_id}/plugins/{package}` | site_id:R,package:R,plugin_params:O |  |
| PUT | `/sites/{site_id}/rollback` | - |  |
| PUT | `/sites/{site_id}/services/{addon}/instances/{instance_id}` | config:R |  |
| PUT | `/sites/{site_id}/snippets/{snippet_id}` | snippet:R |  |
| PUT | `/sites/{site_id}/traffic_splits/{split_test_id}` | branch_tests:R |  |
| PUT | `/sites/{site_id}/unlink_repo` | - |  |
| PUT | `/{account_slug}/members/{member_id}` | accountUpdateMemberSetup:R |  |

## B. bundle 内部端点(58 条)

| 方法 | 路径 | query 参数 | 调用方 | 附近函数 |
|---|---|---|---|---|
| ? | `/.netlify/builders/versions` | - | app | - |
| ? | `/.netlify/functions/fetch-build-plugins` | - | app | l |
| ? | `/.netlify/functions/fetch-extensions` | - | app | l |
| ? | `/.netlify/functions/manage-extension-proxy` | - | app | l |
| ? | `/.netlify/images` | - | ui | m |
| ? | `/access-control/analytics-api` | - | app | A |
| ? | `/access-control/bb-api` | - | app | A |
| ? | `/api/agent-runners/status` | - | app | l |
| ? | `/v1/input` | - | helpers | O |
| DELETE | `/.netlify/functions/delete-configurations-for-site` | - | app | - |
| DELETE | `/.netlify/functions/extensions-connections` | - | lib | u |
| DELETE | `/.netlify/functions/fetch-site-configuration` | - | app | D |
| GET | `/.netlify/builders/notifications` | - | actions | f |
| GET | `/.netlify/functions/FUNCTION-NAME` | - | app | at |
| GET | `/.netlify/functions/fetch-integration-hub` | - | app | l |
| GET | `/.netlify/functions/generate-bandwidth-usage-csv?` | - | app | l |
| GET | `/.netlify/functions/git` | - | actions | m |
| GET | `/.netlify/functions/handler/on-disable?` | - | lib | u |
| GET | `/.netlify/functions/hubspot` | - | app | s |
| GET | `/.netlify/functions/verify?domain=` | domain | actions | Y,tN |
| GET | `/.netlify/functions/workflow-ui` | - | lib | u |
| GET | `/.netlify/identity` | - | app | - |
| GET | `/.netlify/large-media` | - | app | kM |
| GET | `/access-control/create-api` | - | lib | t |
| GET | `/access-control/generate-access-control-token` | - | helpers,lib | M |
| GET | `/api/deploy-diagnostics` | - | app | eF |
| GET | `/api/experiments` | - | lib | u |
| GET | `/api/v2/${t}` | - | monitoring | rj |
| GET | `/spark-proxy/api/v1/knowledge/?scopes=` | scopes | app | g |
| POST | `/.netlify/functions/agent-runner-file-delete?accountId=` | accountId | app | - |
| POST | `/.netlify/functions/bitbucket-self-hosted` | - | lib | t |
| POST | `/.netlify/functions/contact-sales` | - | app | l |
| POST | `/.netlify/functions/create-payment-customer` | - | lib | jl |
| POST | `/.netlify/functions/database-query` | - | app | - |
| POST | `/.netlify/functions/delete-all-team-installations-for-team` | - | app | - |
| POST | `/.netlify/functions/event-observed` | - | app | t |
| POST | `/.netlify/functions/extension-proxy` | - | app | - |
| POST | `/.netlify/functions/fetch-extension` | - | app | - |
| POST | `/.netlify/functions/fetch-extension-host-site-sdk-version` | - | app | - |
| POST | `/.netlify/functions/fetch-installed-extensions-for-team` | - | app | - |
| POST | `/.netlify/functions/fetch-relevant-installed-extensions-for-site` | - | app | - |
| POST | `/.netlify/functions/handler/on-disconnect` | - | lib | - |
| POST | `/.netlify/functions/identeer-proxy` | - | app | l |
| POST | `/.netlify/functions/install-extension` | - | app | - |
| POST | `/.netlify/functions/labs-list` | - | app | - |
| POST | `/.netlify/functions/labs-toggle` | - | app | - |
| POST | `/.netlify/functions/ntli-extension-dev-auth-verify` | - | lib | u |
| POST | `/.netlify/functions/private-integration-create?teamId=` | teamId | actions | a |
| POST | `/.netlify/functions/support-tickets` | - | app | l |
| POST | `/.netlify/functions/uninstall-extension` | - | app | - |
| POST | `/.netlify/functions/update-payment-customer` | - | lib | jl |
| POST | `/.netlify/functions/update-payment-customer-3ds-challenge` | - | lib | - |
| POST | `/.netlify/functions/validate-address` | - | lib | - |
| POST | `/access-control/set-auth` | - | lib | F |
| POST | `/api/agent-runner-file-upload?accountId=` | accountId | app | l |
| POST | `/api/v1` | - | lib | - |
| POST | `/spark-proxy/api/prompt-templates` | - | app | t |
| POST | `/spark-proxy/api/v1/knowledge/?scopes=` | scopes | app | h |

## C. 未出现在 OpenAPI 中的端点(58 条,重点)

| 方法 | 路径 | query 参数 | 调用方 | 附近函数 |
|---|---|---|---|---|
| ? | `/.netlify/builders/versions` | - | app | - |
| ? | `/.netlify/functions/fetch-build-plugins` | - | app | l |
| ? | `/.netlify/functions/fetch-extensions` | - | app | l |
| ? | `/.netlify/functions/manage-extension-proxy` | - | app | l |
| ? | `/.netlify/images` | - | ui | m |
| ? | `/access-control/analytics-api` | - | app | A |
| ? | `/access-control/bb-api` | - | app | A |
| ? | `/api/agent-runners/status` | - | app | l |
| ? | `/v1/input` | - | helpers | O |
| DELETE | `/.netlify/functions/delete-configurations-for-site` | - | app | - |
| DELETE | `/.netlify/functions/extensions-connections` | - | lib | u |
| DELETE | `/.netlify/functions/fetch-site-configuration` | - | app | D |
| GET | `/.netlify/builders/notifications` | - | actions | f |
| GET | `/.netlify/functions/FUNCTION-NAME` | - | app | at |
| GET | `/.netlify/functions/fetch-integration-hub` | - | app | l |
| GET | `/.netlify/functions/generate-bandwidth-usage-csv?` | - | app | l |
| GET | `/.netlify/functions/git` | - | actions | m |
| GET | `/.netlify/functions/handler/on-disable?` | - | lib | u |
| GET | `/.netlify/functions/hubspot` | - | app | s |
| GET | `/.netlify/functions/verify?domain=` | domain | actions | Y,tN |
| GET | `/.netlify/functions/workflow-ui` | - | lib | u |
| GET | `/.netlify/identity` | - | app | - |
| GET | `/.netlify/large-media` | - | app | kM |
| GET | `/access-control/create-api` | - | lib | t |
| GET | `/access-control/generate-access-control-token` | - | helpers,lib | M |
| GET | `/api/deploy-diagnostics` | - | app | eF |
| GET | `/api/experiments` | - | lib | u |
| GET | `/api/v2/${t}` | - | monitoring | rj |
| GET | `/spark-proxy/api/v1/knowledge/?scopes=` | scopes | app | g |
| POST | `/.netlify/functions/agent-runner-file-delete?accountId=` | accountId | app | - |
| POST | `/.netlify/functions/bitbucket-self-hosted` | - | lib | t |
| POST | `/.netlify/functions/contact-sales` | - | app | l |
| POST | `/.netlify/functions/create-payment-customer` | - | lib | jl |
| POST | `/.netlify/functions/database-query` | - | app | - |
| POST | `/.netlify/functions/delete-all-team-installations-for-team` | - | app | - |
| POST | `/.netlify/functions/event-observed` | - | app | t |
| POST | `/.netlify/functions/extension-proxy` | - | app | - |
| POST | `/.netlify/functions/fetch-extension` | - | app | - |
| POST | `/.netlify/functions/fetch-extension-host-site-sdk-version` | - | app | - |
| POST | `/.netlify/functions/fetch-installed-extensions-for-team` | - | app | - |
| POST | `/.netlify/functions/fetch-relevant-installed-extensions-for-site` | - | app | - |
| POST | `/.netlify/functions/handler/on-disconnect` | - | lib | - |
| POST | `/.netlify/functions/identeer-proxy` | - | app | l |
| POST | `/.netlify/functions/install-extension` | - | app | - |
| POST | `/.netlify/functions/labs-list` | - | app | - |
| POST | `/.netlify/functions/labs-toggle` | - | app | - |
| POST | `/.netlify/functions/ntli-extension-dev-auth-verify` | - | lib | u |
| POST | `/.netlify/functions/private-integration-create?teamId=` | teamId | actions | a |
| POST | `/.netlify/functions/support-tickets` | - | app | l |
| POST | `/.netlify/functions/uninstall-extension` | - | app | - |
| POST | `/.netlify/functions/update-payment-customer` | - | lib | jl |
| POST | `/.netlify/functions/update-payment-customer-3ds-challenge` | - | lib | - |
| POST | `/.netlify/functions/validate-address` | - | lib | - |
| POST | `/access-control/set-auth` | - | lib | F |
| POST | `/api/agent-runner-file-upload?accountId=` | accountId | app | l |
| POST | `/api/v1` | - | lib | - |
| POST | `/spark-proxy/api/prompt-templates` | - | app | t |
| POST | `/spark-proxy/api/v1/knowledge/?scopes=` | scopes | app | h |
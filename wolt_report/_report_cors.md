# 标题 必填
title: Permissive CORS Policy on gatekeeper.wolt.com Allows Arbitrary Cross-Origin Read with Credentials
# 资产 必填
Asset: *.wolt.com (WILDCARD)
# 严重程度 必填
Severity: HIGH
# 弱点 必填
Weakness: CWE-942
# 描述 必填
Description
    ## Summary:
    The Gatekeeper API at `gatekeeper.wolt.com` implements a permissive cross-origin resource sharing (CORS) policy that reflects arbitrary `Origin` request header values in the `Access-Control-Allow-Origin` response header, combined with `Access-Control-Allow-Credentials: true`. This configuration allows any external website to make authenticated cross-origin requests to Gatekeeper endpoints and read the responses, violating the Same-Origin Policy protections that normally prevent such cross-domain data access.

    This CORS misconfiguration (CWE-942) is particularly severe when combined with the hardcoded `GATEKEEPER_API_KEY` disclosed in the separate report — an attacker can host a malicious page that silently reads corporate admin data from any browser that has visited corporate.wolt.com.

    ## Steps To Reproduce:
    1. Send an OPTIONS preflight request with an arbitrary attacker-controlled origin:
       1. `curl -v -X OPTIONS https://gatekeeper.wolt.com/v1/corporate_admin -H "Origin: https://evil.com" -H "Access-Control-Request-Method: GET"`

    2. Observe the response includes:
       - `Access-Control-Allow-Origin: https://evil.com`
       - `Access-Control-Allow-Credentials: true`
       - `Access-Control-Allow-Methods: DELETE, GET, HEAD, OPTIONS, PATCH, POST, PUT`
       - `Access-Control-Allow-Headers: x-api-key, content-type`

    3. Repeat with `Origin: null` and confirm it is also reflected:
       1. `curl -v -X OPTIONS https://gatekeeper.wolt.com/v1/corporate_admin -H "Origin: null" -H "Access-Control-Request-Method: GET"`

    4. Verify the same behavior across all v1 endpoints:
       1. `/v1/corporates`, `/v1/organizations`, `/v1/users`, `/v1/alerts`, `/v1/delivery-orders`

    ## Supporting Material/References:
    * CWE-942: Permissive Cross-domain Policy with Untrusted Domains
    * The `Vary: Origin` header is correctly set, but this only ensures proper caching behavior — it does not mitigate the security issue
    * All Gatekeeper v1 paths share identical CORS configuration
    * The `Access-Control-Allow-Credentials: true` flag is the critical escalation factor, enabling cookie/token-based credential exposure
# 影响 必填
Impact:
    An attacker exploiting this CORS misconfiguration can:

    * Host a malicious webpage at any domain that, when visited by a Wolt corporate administrator who is already authenticated to the Gatekeeper portal, silently executes authenticated API requests to `gatekeeper.wolt.com` and exfiltrates the responses — including corporate customer data, delivery orders, admin user records, and billing information
    * Combine the CORS misconfiguration with the exposed GATEKEEPER_API_KEY to make browser-based cross-origin requests even without pre-existing authentication, since the `x-api-key` header is explicitly allowed in `Access-Control-Allow-Headers`
    * Perform credentialed `DELETE`, `PUT`, and `PATCH` operations cross-origin, enabling data modification and deletion attacks against corporate admin resources
    * The `Origin: null` acceptance means even sandboxed documents (data: URIs, sandboxed iframes) can trigger cross-origin requests, expanding the attack surface
# 附件 非必填
Attachments:

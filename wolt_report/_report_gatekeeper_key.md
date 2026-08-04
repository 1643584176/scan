# 标题 必填
title: Hardcoded Gatekeeper API Key in corporate.wolt.com Production Frontend
# 资产 必填
Asset: corporate.wolt.com (URL)
# 严重程度 必填
Severity: CRITICAL
# 弱点 必填
Weakness: CWE-798
# 描述 必填
Description
    ## Summary:
    The corporate.wolt.com production frontend page embeds an HTML `<script>` block containing a variable assignment `window.__env` with a base64-encoded JSON configuration payload. Decoding this payload reveals 30+ production environment variables including a fully functional Gatekeeper API key (`GATEKEEPER_API_KEY`), multiple internal API endpoints, Google Maps API key, and Mapbox token.

    The `GATEKEEPER_API_KEY` is a 40-character alphanumeric key intended for server-side authentication to `gatekeeper.wolt.com/v1/corporate_admin` — Wolt's enterprise authorization gateway that manages corporate customer accounts, organizations, delivery orders, billing, admin user permissions, and address books. By design this key should never reach client-side browsers; its presence in the public HTML constitutes a Hardcoded Credentials vulnerability (CWE-798) with a direct, authenticated attack path to Wolt's corporate administration backend.

    ## Steps To Reproduce:
    1. Download the corporate.wolt.com landing page and extract the base64-encoded `window.__env` payload:
       1. `curl -s https://corporate.wolt.com/ | grep -oP "window\.__env\s*=\s*'\K[^']+" > env_b64.txt`
       2. `base64 -d env_b64.txt | python3 -m json.tool`

    2. Confirm the API key is present in the decoded JSON under the key `GATEKEEPER_API_KEY`.

    3. Verify the key is accepted by the Gatekeeper endpoint:
       1. `curl -v -X OPTIONS https://gatekeeper.wolt.com/v1/corporate_admin -H "Origin: https://evil.com" -H "Access-Control-Request-Method: GET" -H "x-api-key: [REDACTED]"`

    4. Confirm the server responds with the following headers that enable cross-origin exploitation:
       - `Access-Control-Allow-Origin: https://evil.com`
       - `Access-Control-Allow-Credentials: true`
       - `Access-Control-Allow-Headers: x-api-key`
       - `Access-Control-Allow-Methods: DELETE, GET, HEAD, OPTIONS, PATCH, POST, PUT`

    ## Supporting Material/References:
    * CWE-798: Use of Hardcoded Credentials
    * The `GATEKEEPER_API_KEY` value has been redacted from the PoC commands above; the full plaintext key was observed in the production deployment of corporate.wolt.com (APP_VERSION 4.8.0, APP_ENV production)
    * Additional endpoints accessible with the same key: `gatekeeper.wolt.com/v1/corporates`, `gatekeeper.wolt.com/v1/organizations`, `gatekeeper.wolt.com/v1/users`
    * All Gatekeeper v1 endpoints share the same CORS misconfiguration (echoed ACAO + ACAC:true)
# 影响 必填
Impact:
    An attacker who obtains the exposed GATEKEEPER_API_KEY (any visitor to corporate.wolt.com has it) can:

    * Authenticate to the Gatekeeper enterprise admin API at `gatekeeper.wolt.com/v1/corporate_admin` with full method access (GET, POST, PUT, PATCH, DELETE)
    * Access and modify corporate customer records, delivery orders, billing data, admin user permissions, and organization settings through `/v1/corporates`, `/v1/organizations`, `/v1/users`, and `/v1/delivery-orders`
    * Exploit the CORS misconfiguration (`Access-Control-Allow-Origin` reflects arbitrary origins + `Access-Control-Allow-Credentials: true`) to perform cross-origin attacks from any external domain — a malicious website can execute authenticated API calls against Gatekeeper on behalf of visiting corporate.wolt.com users
    * Leverage the same key to discover and probe additional internal services whose URIs are also disclosed in the `__env` payload: `corporate-service.wolt.com`, `daas-public-api.wolt.com`, `wolf.wolt.com`, `legitimizer.wolt.com`, and `merchant-payout-service.wolt.com`
# 附件 非必填
Attachments:

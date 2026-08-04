# 标题 必填
title: Internal Server-Side Path Disclosure via Validation Error Messages on Checkout API
# 资产 必填
Asset: *.wolt.com (WILDCARD)
# 严重程度 必填
Severity: LOW
# 弱点 必填
Weakness: CWE-209
# 描述 必填
Description
    ## Summary:
    The `/order-xp/web/v2/pages/checkout` endpoint at `consumer-api.wolt.com` — the same endpoint affected by the price manipulation vulnerability — consistently includes internal server-side file paths in its JSON validation error responses. Specifically, every malformed or incomplete POST request to this endpoint returns a `details` field containing the absolute server path `File "/app/orderxp/pages/checkout/v2/api.py", line 349`, followed by the function name `get_checkout_page_web`.

    This is CWE-209: Generation of Error Message Containing Sensitive Information. The error messages reveal the internal directory structure (`/app/orderxp/pages/checkout/v2/`), the Python module name (`api.py`), the exact line number where validation occurs (line 349), and the internal function name (`get_checkout_page_web`). This information assists an attacker in understanding the server-side application architecture, framework, and code organization — intelligence that can be used to craft more targeted attacks against the backend.

    ## Steps To Reproduce:
    1. Send a POST request to the checkout endpoint with an empty body:
       1. `curl -v -X POST https://consumer-api.wolt.com/order-xp/web/v2/pages/checkout -H "Content-Type: application/json" -d '{}'`

    2. Observe the response contains a full server-side file path:
       1. `{"details":"1 validation error:\n  {'type': 'missing', 'loc': ('body', 'purchase_plan'), 'msg': 'Field required', 'input': {}}\n\n  File \"/app/orderxp/pages/checkout/v2/api.py\", line 349, in get_checkout_page_web\n    POST /web/v2/pages/checkout"}`

    3. Repeat with various invalid payloads — the path is disclosed in every case:
       1. `-d 'null'` → triggers `'type': 'missing', 'loc': ('body',)` 
       2. `-d '[]'` → triggers `'type': 'model_attributes_type'`
       3. `-d '"bad"'` → triggers `'type': 'json_invalid'`
       4. All responses include `File "/app/orderxp/pages/checkout/v2/api.py", line 349, in get_checkout_page_web`

    4. Confirm the same behavior occurs when providing partially valid JSON with wrong types on nested fields:
       1. Send `{"purchase_plan": {"menu_items": [{"restrictions": {}}]}}`
       2. The response includes: `File "/app/orderxp/pages/checkout/v2/api.py", line 349, in get_checkout_page_web`

    ## Supporting Material/References:
    * CWE-209: Generation of Error Message Containing Sensitive Information
    * Affected endpoint: `POST https://consumer-api.wolt.com/order-xp/web/v2/pages/checkout`
    * Disclosed information:
        * Internal directory: `/app/orderxp/pages/checkout/v2/`
        * Module file: `api.py`
        * Function: `get_checkout_page_web`
        * Error location: line 349
    * This endpoint already has a validated HIGH severity finding (price manipulation); the path disclosure is a separate, lower-severity information leak embedded in the same error responses
    * The path is disclosed regardless of input validity — empty body, null, array, string, and partially valid JSON all trigger it
# 影响 必填
Impact:
    An unauthenticated attacker can:

    * Map the internal server-side directory structure of the Wolt OrderXP backend (`/app/orderxp/pages/checkout/v2/api.py`), gaining architectural intelligence about Python-based microservice organization
    * Identify the backend framework (Pydantic/FastAPI based on the `{'type': ..., 'loc': ..., 'msg': ..., 'input': ...}` error format) and the exact validation layer entry point (line 349 in `api.py`)
    * Correlate this architectural information with other vulnerabilities — for example, knowing the exact Pydantic validation schema helps an attacker craft payloads that bypass client-side restrictions while satisfying server-side type checking (as demonstrated in the price manipulation finding)
    * Use the disclosed paths to infer the existence of related endpoints (e.g., `/app/orderxp/pages/orders/`, `/app/orderxp/pages/order/`) and probe for additional attack surface
# 附件 非必填
Attachments:

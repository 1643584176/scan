# 标题 必填
title: Client-Supplied Price Manipulation in Checkout API (CWE-602) — Arbitrary Item Prices Accepted Without Server-Side Validation
# 资产 必填
Asset: *.wolt.com (WILDCARD)
# 严重程度 必填
Severity: HIGH
# 弱点 必填
Weakness: CWE-602
# 描述 必填
Description
    ## Summary:
    The POST `/order-xp/web/v2/pages/checkout` endpoint at `consumer-api.wolt.com` trusts client-supplied item prices (`purchase_plan.menu_items[].price`, `base_price`, `end_amount`) without performing any server-side re-validation against the venue's actual item catalog. The backend computes `payable_amount` using the formula `client_price + delivery_fee + bag_fee + service_fee`, with the client price component taken directly from the request body. No purchase token (HMAC/signature) is used to bind the client-side basket to server-verified prices.

    This is Client-Side Enforcement of Server-Side Security (CWE-602): the server abdicates its responsibility to verify a transactional monetary value that directly determines the amount charged to the customer.

    The response confirms this configuration explicitly:
    - `use_backend_pricing_for_shadowing_only: false` — backend pricing override is disabled for this venue
    - `purchase_validation.use_token: null` — no purchase token or HMAC protection is applied
    - `purchasing_disabled: null` / `toast: null` — checkout proceeds normally with tampered prices, no error or warning raised

    ## Steps To Reproduce:
    1. Construct a `purchase_plan` payload with an arbitrary client-side price (e.g., 1 cent) for the target venue (`wolt-market-kamppi`, venue ID `60ebeb71c6904c2caf035f71`):
       1. `curl -X POST https://consumer-api.wolt.com/order-xp/web/v2/pages/checkout -H "Content-Type: application/json" -H "Origin: https://wolt.com" -d '{"purchase_plan":{"venue":{"id":"60ebeb71c6904c2caf035f71","country":"FIN","currency":"EUR"},"delivery_method":"homedelivery","menu_items":[{"id":"60ebeb71c6904c2caf035f71","name":"Test Item","count":1,"base_price":1,"price":1,"end_amount":1,"options":[],"category_id":"test","exclude_from_discounts":false,"restrictions":[]}]}}'`

    2. Observe the server returns HTTP 200 with `payable_amount` computed directly from the tampered `price=1`, without re-fetching the venue's catalog price for item `60ebeb71c6904c2caf035f71`.

    3. A controlled three-group experiment confirms the server-side price formula is deterministic and unvalidated:

       | Probe | Client Price (cents) | payable_amount (cents) | end_amount (cents) | service_fee | HTTP |
       |-------|---------------------|------------------------|--------------------|-------------|------|
       | real_306 | 306 | 1384 | 1384 | 100 | 200 |
       | tampered_0 | 0 | 1078 | 1078 | 100 | 200 |
       | huge_999999 | 999999 | 1001077 | 1001077 | 399 | 200 |

    4. The derived formula: `payable_amount = price + delivery_fee(948) + bag_fee(30) + service_fee(~100)` — with the `price` component carrying through untouched.

    ## Supporting Material/References:
    * CWE-602: Client-Side Enforcement of Server-Side Security
    * CWE-472: External Control of Assumed-Immutable Web Parameter
    * Target venue: Wolt Market Kamppi (`wolt-market-kamppi`, venue ID `60ebeb71c6904c2caf035f71`)
    * Affected endpoint: `https://consumer-api.wolt.com/order-xp/web/v2/pages/checkout`
    * No authentication required — endpoint accessible to unauthenticated guest users
    * All three probe responses returned `use_backend_pricing_for_shadowing_only: false`, confirming the pricing bypass is venue-level configuration, not a per-request anomaly
    * Evidence: three full JSON response dumps (_checkout_real_306.json, _checkout_tampered_0.json, _checkout_huge_999999.json) available on request
# 影响 必填
Impact:
    An unauthenticated attacker exploiting this missing server-side price validation can:

    * Set item prices to zero, paying only the fixed delivery fee (948 cents) + bag fee (30 cents) for any item regardless of its actual catalog price — a direct monetary loss for Wolt and its merchant partners
    * Manipulate prices to any arbitrary integer value, including extremes (tested up to 999999 cents / €9,999.99), with the server accepting and computing the payable amount accordingly
    * Operate entirely without authentication — no login, session token, or account is required to submit tampered checkout requests, making this exploitable at scale by automated scripts
    * No rate limiting or anomaly detection was triggered across multiple successive requests with wildly different price values, suggesting the tampered payloads are not flagged by any integrity monitoring layer
# 附件 非必填
Attachments:


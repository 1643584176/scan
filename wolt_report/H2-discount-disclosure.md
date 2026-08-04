# 标题 必填
title: Unauthenticated Exposure of Venue Discount Campaigns and Delivery Pricing Configuration via Venue Dynamic API
# 资产 必填
Asset: *.wolt.com (WILDCARD)
# 严重程度 必填
Severity: MEDIUM
# 弱点 必填
Weakness: CWE-200
# 描述 必填
Description
    ## Summary:
    The endpoint `GET /order-xp/web/v1/venue/slug/{venue_slug}/dynamic/` at `consumer-api.wolt.com` — accessible without any authentication — returns a comprehensive JSON payload that includes the full configuration of all active discount/promotion campaigns for the venue, along with the complete delivery pricing formula. The `venue_raw.discounts` array exposes 11 active campaigns for Wolt Market Kamppi, each detailing the discount type (percentage off, fixed amount, buy-N-get-M, free delivery), exact discount values, the full list of qualifying item IDs, and all triggering conditions (minimum basket, delivery method, distance range, time restrictions, Wolt Plus requirement). The `venue_raw.delivery_specs.delivery_pricing` field exposes the proprietary delivery fee formula including `base_price`, `price_ranges` coefficients, and `distance_ranges` tier definitions.

    This is Exposure of Sensitive Information to an Unauthorized Actor (CWE-200): the venue API serves internal campaign and pricing configuration to every unauthenticated visitor, providing competitors with complete visibility into Wolt's promotional strategy and delivery cost structure.

    ## Steps To Reproduce:
    1. Request the venue dynamic endpoint for any Wolt Market venue without authentication:
       1. `curl -s "https://consumer-api.wolt.com/order-xp/web/v1/venue/slug/wolt-market-kamppi/dynamic/?selected_delivery_method=homedelivery" -H "Origin: https://wolt.com" | python3 -c "import sys,json; d=json.load(sys.stdin); print(len(d['venue_raw']['discounts']),'discounts'); [print(json.dumps(x['effects'],indent=2)) for x in d['venue_raw']['discounts'][:3]]"`

    2. Observe the response contains 11 discount campaigns in `venue_raw.discounts`, each with:
       - `id`: unique campaign identifier (e.g. `venue_campaign:6a4f437f001d9efc9c621570`)
       - `effects`: exact discount mechanics:
         - `item_discount` with `fraction` (e.g. 0.2 = 20% off) + list of qualifying item IDs
         - `basket_discount` with `amount` in cents (e.g. 500 = €5.00 off)
         - `delivery_discount` with `fraction: 1.0` (100% free delivery)
         - `free_items` with `buy: N, get: M` + item list
       - `conditions`: triggering rules including `basket_contains`, `delivery_methods`, `min_distance`, `max_distance`, `weekly_time_restrictions`, `has_wolt_plus`, `payment_method`

    3. Extract the delivery pricing formula from `venue_raw.delivery_specs.delivery_pricing`:
       1. `curl -s "https://consumer-api.wolt.com/order-xp/web/v1/venue/slug/wolt-market-kamppi/dynamic/?selected_delivery_method=homedelivery" -H "Origin: https://wolt.com" | python3 -c "import sys,json; d=json.load(sys.stdin); dp=d['venue_raw']['delivery_specs']['delivery_pricing']; print('base_price:',dp['base_price']); print('price_ranges:',json.dumps(dp['price_ranges'],indent=2)); print('distance_ranges:',json.dumps(dp['distance_ranges'],indent=2))"`

    4. Confirm the endpoint is fully unauthenticated — no cookies, tokens, or API keys are required for any of the above requests.

    ## Supporting Material/References:
    * CWE-200: Exposure of Sensitive Information to an Unauthorized Actor
    * Affected endpoint: `https://consumer-api.wolt.com/order-xp/web/v1/venue/slug/{slug}/dynamic/`
    * Tested venue: Wolt Market Kamppi (`wolt-market-kamppi`) — 11 campaigns, 7 distance pricing tiers, 3 basket price tiers
    * Campaign types exposed: percentage-off items (20%, 30%), fixed basket discount (€5.00), free delivery (100% off), buy-3-get-1-free, buy-4-get-1-free
    * Delivery formula: `base_price=149` cents, with polynomial coefficients `a` and `b` per price tier and per distance tier
    * All data is served in the same response that renders the public venue page — no separate admin endpoint involved
# 影响 必填
Impact:
    An unauthenticated party accessing this endpoint can:

    * Enumerate all active promotional campaigns for any Wolt venue, including exact discount values (percentage, fixed amount, free items), the complete list of qualifying product IDs, and all triggering conditions — providing competitors with actionable intelligence to undercut Wolt's pricing strategy in real-time
    * Reverse-engineer Wolt's proprietary delivery pricing formula, including the base price, polynomial coefficients per basket value tier, and 7 distance-based pricing tiers — enabling competitors to model and replicate Wolt's delivery cost structure
    * Monitor campaign changes over time by polling the endpoint periodically, building a historical database of Wolt's promotional cadence and seasonal strategies without any authentication or rate-limiting barriers
    * Cross-reference the exposed item IDs with public menu data to determine exactly which products are on promotion, when, and under what conditions — information normally guarded as trade secrets in the food delivery industry
# 附件 非必填
Attachments:


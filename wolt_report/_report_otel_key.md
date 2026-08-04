# 标题 必填
title: Hardcoded OpenTelemetry Collector API Key in converse-web-static.wolt.com Client-Side JavaScript
# 资产 必填
Asset: *.wolt.com (WILDCARD)
# 严重程度 必填
Severity: HIGH
# 弱点 必填
Weakness: CWE-798
# 描述 必填
Description
    ## Summary:
    The file `converse-web-static.wolt.com/conveyer/frame.js` — a client-side JavaScript bundle served to all visitors of corporate.wolt.com — hardcodes an OpenTelemetry Collector API key (`OTEL_COLLECTOR_CLIENT_API_KEY`) as a runtime configuration value. This key is a 64-character hex string intended to authenticate telemetry data submissions (traces, metrics, logs) to Wolt's internal OpenTelemetry Collector pipeline.

    The same JavaScript file also exposes the production Sentry DSN and reveals the existence of a development/staging environment at `dev.woltapi.com`, including its full infrastructure URL pattern.

    ## Steps To Reproduce:
    1. Retrieve the client-side JavaScript bundle:
       1. `curl -s https://converse-web-static.wolt.com/conveyer/frame.js`

    2. Extract the hardcoded configuration object from the bundle:
       1. The relevant section is: `var c={NODE_ENV:"production",APP_ENV:"production",...,OTEL_COLLECTOR_CLIENT_API_KEY:"[REDACTED]"`

    3. Confirm the key is exposed in the production deployment:
       1. The file returns HTTP 200 and is loaded by corporate.wolt.com's main SPA bundle

    ## Supporting Material/References:
    * CWE-798: Use of Hardcoded Credentials
    * The key value has been redacted from this report; plaintext was observed in production build version `e74d97ced57fb39caf69387cce34ab37329c1c3a`
    * The same file also exposes: `SENTRY_DSN`, `NODE_ENV`, `APP_ENV`, `APP_VERSION`
    * Development environment URL pattern is also disclosed: `converse-web-static.development.dev.woltapi.com/conveyer/`
# 影响 必填
Impact:
    An attacker with access to the `OTEL_COLLECTOR_CLIENT_API_KEY` can:

    * Submit forged telemetry data (traces, metrics, logs) into Wolt's internal OpenTelemetry pipeline, potentially corrupting monitoring, alerting, and observability data used by Wolt's engineering and operations teams
    * Exploit the key to probe for the OpenTelemetry Collector endpoint (gRPC/HTTP) which may be accessible from within Wolt's network or via the exposed development environment at `dev.woltapi.com`
    * Leverage the leaked Sentry DSN and development infrastructure URLs to expand the attack surface against Wolt's staging and development environments
    * The key exists in a publicly accessible S3-backed static asset with no access control restrictions — any visitor or automated scanner can retrieve it without authentication
# 附件 非必填
Attachments:

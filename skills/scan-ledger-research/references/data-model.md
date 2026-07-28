# AssetTrace data model

## Cache identity

An analysis result is reusable only when all four values match:

1. Asset revision fingerprint
2. Detector key
3. Detector semantic version
4. Detector configuration hash

The revision fingerprint covers the response body digest, final URL, status code, and persisted analysis-relevant headers. A `304 Not Modified` response confirms the latest revision without creating a new one.

## Core records

- `projects`: Root URL and domain suffix allowed for automatic child-asset fetching.
- `assets`: Canonical page, JavaScript, endpoint, or source-map URLs.
- `asset_revisions`: Immutable fetched states backed by content-addressed blobs.
- `asset_edges`: Discovery relations such as `loads-script` and `references-endpoint`.
- `scan_runs`: One user-requested analysis batch.
- `analysis_jobs`: One detector applied to one asset revision in one run. A reused job points to its source job.
- `findings`: Stable, deduplicated issues with first-seen, last-seen, and resolved run IDs.
- `knowledge_items`: Draft or approved generalized records derived from findings.

## State rules

- Record a new run even when every analysis job is reused.
- Re-run a detector when its version changes.
- Re-run all applicable detectors when the asset revision fingerprint changes.
- Mark an old finding resolved only after a fresh completed detector job does not emit its fingerprint.
- Reused jobs keep linked findings open and advance their last-seen run.
- Treat the recorded host and its subdomains as in scope; never expand to a parent or sibling domain.
- Record out-of-scope discoveries, but do not fetch them automatically.

# AssetTrace

AssetTrace records URL and JavaScript security analysis as an asset ledger. It reuses a prior detector result only when the asset revision, detector key, detector version, and detector configuration all match.

## Run

```powershell
python -m pip install -r requirements.txt
python app.py
```

Open `http://127.0.0.1:8000`. API documentation is available at `/docs`.

Private and loopback targets are blocked by default. For an explicitly authorized local test environment:

```powershell
$env:ASSETTRACE_ALLOW_PRIVATE_TARGETS = "1"
python app.py
```

## Structure

- `assettrace/storage.py`: SQLite asset, revision, job, finding, and knowledge ledger.
- `assettrace/fetcher.py`: bounded HTTP fetching, conditional requests, redirect validation, and SSRF guard.
- `assettrace/engine.py`: incremental scheduling and cache reuse.
- `assettrace/detectors/`: versioned passive detectors.
- `skills/scan-ledger-research/`: project-level workflow and approved reusable patterns.
- `data/assettrace.db`: new runtime database; the legacy `data/scan.db` is not modified.

Run tests with:

```powershell
python -m unittest discover -s tests -v
```

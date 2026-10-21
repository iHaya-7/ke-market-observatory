# Baseline Snapshot Manifest

## Capture identity

- Snapshot ID: `20261021T110343966Z-ee5bd15f`
- Capture time: `2026-10-21T11:03:43.966Z`
- Repository HEAD: `ee5bd15ff52b6a88e15a2dafab6886422980f557`
- Worktree before capture: clean; `git status --porcelain=v1` returned no changes.
- The approved `AS_IS_AUDIT.md` records HEAD `002525b2e08f610206b205374ad2244785b9c088`, which differs from the current snapshot HEAD. This snapshot is pinned to the actual current HEAD above; the audit was not changed.

The worktree state describes the repository immediately before creating this snapshot. The newly created snapshot files are uncommitted and are not part of that pre-capture state.

## Preserved source files

Files were copied as raw bytes. The original and copied sizes and SHA-256 hashes match:

| Original source path | Snapshot path | Bytes | SHA-256 (source and copy) |
|---|---|---:|---|
| `data/curated.json` | `data/curated.json` | 56,944 | `2fd14e04420fe94d62ce2952b0a3e04662709b27bd23d9134f2a2e7424884b46` |
| `data/auto_records.json` | `data/auto_records.json` | 45,113 | `6171360dee49f034efc0e60caa7ad136801d4ba89a35e1ae6243c77de1703795` |
| `data/review_decisions.json` | `data/review_decisions.json` | 43 | `f425ac6675a1a1850c0f066971a97aadb3913670356b11860e85ce7e02cbd47d` |
| `public/data/market.json` | `public/data/market.json` | 92,238 | `17fa523c0e13341ca499750da7cac4958454ac4e1bf93a403cf6a6dc26ae27e0` |

## Code, configuration, and generated dashboard fingerprints

The following files were hashed in place and not copied. Their byte counts and SHA-256 values are in `manifest.json`:

- `scripts/refresh.py`
- `scripts/build_site.py`
- `web/app.js`
- `web/app.css`
- `web/template.html`
- `config/sources.json`
- `.github/workflows/refresh-and-deploy.yml`
- `tests/test_refresh.py`
- `tests/test_build_site.py`

`public/index.html` was not copied. Its recorded SHA-256 is `7909f14c57c8a3d35fbf21c2394e00785cda61a959188f2d6530c567da2a4c6f` (583,060 bytes). The approved audit document was also fingerprinted without modification.

## Published dataset metadata

- `dataVersion`: `502461042f744e2d`
- Stored `publishedAt` and `lastSuccessfulCollectionAt`: `2026-10-21T10:13:37Z`
- Stored `lastContentChangeAt`: `2026-10-20T19:20:27Z`
- Stored source status: all six configured sources report `OK`.
- FX date: `2026-10-20`; rates: SAR 1, USD 3.75, GBP 5.005005, EUR 4.205639.
- FX source and assumptions: Frankfurter reference rates cross-converted through the fixed USD/SAR assumption of 3.75. The complete stored FX object, including status and timestamps, is in `manifest.json`.

The timestamps and source statuses above are values in the frozen JSON, not independently verified live collection results. In particular, the audit's `2026-10-20T19:20:27Z` timestamp is the current data's `lastContentChangeAt`, not its current stored successful-collection timestamp.

## Integrity checks

- All four source JSON files parsed before copying; copied JSON files parsed.
- Each copy matched its source byte-for-byte and by SHA-256.
- The dashboard's embedded JSON seed matches `public/data/market.json`.
- The dashboard's embedded JavaScript matches the current `web/app.js`.
- The published HTML checksum is recorded without copying the HTML.
- No refresh, collection, test suite, build, or deployment was run for this snapshot.

See `manifest.json` for machine-readable paths, hashes, working-tree details, data version, FX metadata, counts, and verification results.

# Baseline snapshot manifest

Snapshot ID: `20261021T110236218Z-ec7c36e4`  
UTC capture: `2026-10-21T11:02:36.218Z`  
Git HEAD: `ee5bd15ff52b6a88e15a2dafab6886422980f557` (branch `main`).

The working tree was clean before snapshot creation: no staged, unstaged, or untracked changes. This task adds only this new snapshot directory and does not commit it. Full pre-capture tracked-file fingerprints and committed-blob hashes are in [manifest.json](manifest.json); a commit hash alone is not used to establish data identity.

## Preserved data

Source paths are relative to the repository root; copies retain the same relative paths inside this snapshot. Original and copied SHA-256 values were calculated separately and match.

| Source and snapshot path | Bytes | Original SHA-256 (= copied SHA-256) |
| --- | ---: | --- |
| `data/curated.json` | 56944 | `2fd14e04420fe94d62ce2952b0a3e04662709b27bd23d9134f2a2e7424884b46` |
| `data/auto_records.json` | 45113 | `6171360dee49f034efc0e60caa7ad136801d4ba89a35e1ae6243c77de1703795` |
| `data/review_decisions.json` | 43 | `f425ac6675a1a1850c0f066971a97aadb3913670356b11860e85ce7e02cbd47d` |
| `public/data/market.json` | 92238 | `17fa523c0e13341ca499750da7cac4958454ac4e1bf93a403cf6a6dc26ae27e0` |

## Implementation fingerprints

Code/configuration are identified by HEAD plus exact working-file SHA-256. No application code is copied. Tests, all bundled fonts, and their license are included because they participate in verification/build reproduction.

| Repository path | SHA-256 |
| --- | --- |
| `.github/workflows/refresh-and-deploy.yml` | `d7eb605bf0f2513f116e5129daf2bf102ba1b778d3b00a5d1dcd7c20ae9c0613` |
| `config/sources.json` | `c5a2948b6cfb241c4e1dd7af4ff1d6e58d0e3e229cad080e2c62ecf1a0c4ad4b` |
| `scripts/build_site.py` | `93f0c8fe70578789ef0c96f051c2eb483a95adb185c5ea29be580ce81144e5dd` |
| `scripts/refresh.py` | `e8ba9dde2539fe778e971b676a3bd4b8d8370b5669f88e4ba561af4e68e678bb` |
| `tests/test_build_site.py` | `f50ab761bf4300e17571f170560319388305422a090aa8952da77b00bdaaca4f` |
| `tests/test_refresh.py` | `64e47453f134f700d00c976cd652e3b51e1ba6abd48bdd5f2e1303f03a91991f` |
| `web/app.css` | `ebd1e931b4af38d3a181a5c016a2f9108f2a2da9c90d5910e357e60e2248a855` |
| `web/app.js` | `a8bc00081d241b38cbc1a611be0368a5d4f89d7e29c839a449b0a4c9bc1ac998` |
| `web/fonts/IBMPlexSansArabic-Bold.woff2` | `db6650a05969c144ab5ab9bb6c3beca6ca4dbb3537bb5f2311c878dd293875b4` |
| `web/fonts/IBMPlexSansArabic-Medium.woff2` | `c72f6986f50ded745d06e71e508096209c52a55a6b3a81029954e33c52ba1dd2` |
| `web/fonts/IBMPlexSansArabic-Regular.woff2` | `74112e1b7bf2e2c547989a4e947a60cba6cd1f9156e0065670134636e717199d` |
| `web/fonts/IBMPlexSansArabic-SemiBold.woff2` | `869b2acd0a9660607a2025f0fe1c640110bf23d33417509328f07722922b8063` |
| `web/fonts/OFL.txt` | `d741e57d5f865e294df801f96b7b5161a88b211df65887e4358d271c9fc5fb4f` |
| `web/template.html` | `3ac44c6779a5c18cea97810d4cf5182ff8ad4a80573554a800148e9cd27f0b14` |

Generated HTML is **not copied**. `public/index.html` SHA-256: `7909f14c57c8a3d35fbf21c2394e00785cda61a959188f2d6530c567da2a4c6f` (583060 bytes). Its existing seed JSON was parsed and deep-equal to the frozen published JSON. Its embedded application script also contains the current source JavaScript. This verifies local artifact consistency, not deployed hosting.

The machine manifest records both committed Git blob SHA-256 and working-file SHA-256. Git `core.autocrlf=true` can make clean checked-out text bytes differ from committed LF bytes. Each file records whether LF-to-CRLF expansion explains the difference. Recover implementation files from this HEAD and verify both identities/line endings; do not assume a commit identifies arbitrary working bytes.

## Stored publication and FX

Published `meta.dataVersion`: `502461042f744e2d`. Stored last successful collection: `2026-10-21T10:13:37Z`; stored publication: `2026-10-21T10:13:37Z`. Capture time is separate and does not renew source evidence.

The approved audit names HEAD `002525b2e08f610206b205374ad2244785b9c088` and an earlier collection. Relevant paths changed between that HEAD and this capture HEAD: `data/auto_records.json`, `public/data/market.json`, `public/index.html`. Rule/configuration/test files are unchanged across those commits; current generated evidence is frozen as found. The previous audit is not modified.

Curated records: 21; retained automatic: 20; published: 26; review items: 30. See [BASELINE_RESULTS.md](BASELINE_RESULTS.md) and machine-readable `results` for detailed distributions, coverage, eligibility, and limitations. No accuracy metrics or labels are created.

Published FX date: `2026-10-20`; rates to SAR: `{"SAR":1,"USD":3.75,"GBP":5.005005,"EUR":4.205639}`. Source: https://frankfurter.dev/; status: `Updated`; configured USD/SAR assumption: 3.75. Full published and curated FX metadata, including labels and timestamps, is preserved in the manifest and copied datasets. These stored rates were not independently reverified. Hold FX constant when isolating Knowledge Engineering effects on eligibility/comparability.

## Integrity and reproduction

All files are exclusively created in a unique timestamp-and-random-suffix directory. Existing snapshots are never overwritten. [SHA256SUMS](SHA256SUMS) seals the four data copies, both manifests, results document, and verifier. It excludes itself to avoid circular hashing. Retain the reported seal digest outside this directory. Checksums detect changes against the seal; this local filesystem is not WORM storage and the seal is not signed. Treat the snapshot as immutable and create a new directory for any later capture.

From the repository root, verify the snapshot independently of current production files:

```text
node knowledge-engineering/00-baseline/snapshots/20261021T110236218Z-ec7c36e4/verify.cjs
```

To additionally compare every pre-existing tracked file and all four original source bytes with the current repository:

```text
node knowledge-engineering/00-baseline/snapshots/20261021T110236218Z-ec7c36e4/verify.cjs --repository .
```

The second command should pass immediately after capture; it should report differences after legitimate future production changes. The first uses preserved data and exact extracted existing frontend fragments and remains usable when production evolves. Both are local, read-only, and dependency-free (Node built-ins; captured CLI runtime v24.16.0). They invoke no collector, full frontend bootstrap, tests that exercise refresh, build, deployment, or network calls.

Capture checks established byte equality, JSON parsing, unchanged original tracked files and HEAD, and matching embedded data. The verifier recomputes seal/data checksums and descriptive results; with `--repository`, it also recomputes every recorded working-file and committed-blob checksum. No live source claims or GitHub execution are verified.

Step 0.2 ends here. Step 0.3 requires review before proceeding.

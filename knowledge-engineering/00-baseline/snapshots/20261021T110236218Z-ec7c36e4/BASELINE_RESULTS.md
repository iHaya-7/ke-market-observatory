# Descriptive baseline results — Step 0.2

Snapshot: `20261021T110236218Z-ec7c36e4`; captured `2026-10-21T11:02:36.218Z` UTC; HEAD `ee5bd15ff52b6a88e15a2dafab6886422980f557`. These are observations from frozen files, **not classification accuracy or source verification**. Machine-readable results and exact source fingerprints are in [manifest.json](manifest.json). No original flags, duplicate groups, or review outcomes were changed.

## Populations and stored flags

| Population | Records | Role approved | Role pending | Role decision missing | Salary eligible true | Salary eligible false | Numeric salary minimum |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| curated | 21 | 21 | 0 | 0 | 1 | 20 | 13 |
| automatic | 20 | 7 | 7 | 6 | 0 | 20 | 3 |
| published | 26 | 26 | 0 | 0 | 1 | 25 | 13 |

Missing role decisions are absent properties, kept distinct from explicit null or pending. Detailed distributions, including any other values, appear in `results.populations.*` in the manifest. Curated approvals, machine approvals, and existing verification flags are not independent Ground Truth. Numeric salary counts do not imply comparable base pay; retained automatic numeric ranges can belong to historical/nonpublished candidates.

Stored salary-basis distributions:

- curated: `{"unknown":8,"base":1,"unverified":2,"estimate":2,"none":8}`.
- automatic: `{"<missing>":6,"none":14}`.
- published: `{"unknown":8,"base":1,"unverified":2,"estimate":2,"none":13}`.

## Existing review outputs

| Category | Items |
| --- | ---: |
| Role relevance | 13 |
| Pay basis | 11 |
| Saudi listing status | 6 |
| **Total** | **30** |

These represent 27 distinct record IDs. Category items, not unique jobs, form the item count. Manual approved IDs: 0; rejected IDs: 0. No reviewer/reviewed-at/outcome-history fields exist. Queue items can refer to records absent from published jobs; pay/status items can refer to published curated records. Queue presence or disappearance is not an accuracy judgment.

## Frontend benchmark eligibility

Safely executed the exact existing `isSalary`, `baseEligible`, `totalEligible`, `monthly`, and `validate` fragments, plus the `validUrl` dependency, from `web/app.js` against a clone of frozen published JSON in an isolated Node VM. The manifest preserves fragment text, SHA-256, source-file hash, and execution method. No full app, browser polling, collection, or network code ran.

Current base-benchmark-eligible count: **1**; record IDs: `KE-007`. Verified-total-pay predicate count: 0. These are existing code decisions, not independently substantiated pay.

| Eligible record | Monthly minimum SAR | Monthly maximum SAR |
| --- | ---: | ---: |
| `KE-007` | 46625 | 77812.5 |

Formula: original amount × frozen SAR FX rate, divided by 12 for Annual; values above precede display rounding. The existing base predicate requires non-Saudi, not pending, employer evidence, explicit eligible/base/verified flags, and usable pay units/FX. It does not require fresh/open status or known experience; historical references can qualify. No mean, median, or inferred market salary range is added.

## Evidence field coverage

Cells are **property present / non-empty value**, counted over curated 21, automatic 20, and published 26 rows. Presence includes null/empty properties; non-empty means non-null and, for strings, nonblank. The manifest also records non-null counts. These counts measure metadata availability, **not verified source support, correct dates, working links, or claim correctness**.

| Field | Curated present / non-empty | Automatic present / non-empty | Published present / non-empty |
| --- | ---: | ---: | ---: |
| `sourceUrl` | 21 / 21 | 20 / 20 | 26 / 26 |
| `extraUrl` | 21 / 8 | 20 / 0 | 26 / 8 |
| `sourceLabel` | 21 / 21 | 20 / 20 | 26 / 26 |
| `sourceId` | 21 / 0 | 20 / 20 | 26 / 7 |
| `sourceJobId` | 0 / 0 | 20 / 20 | 5 / 5 |
| `evidenceType` | 21 / 21 | 20 / 20 | 26 / 26 |
| `evidenceMethod` | 21 / 21 | 20 / 20 | 26 / 26 |
| `origin` | 21 / 21 | 20 / 20 | 26 / 26 |
| `collection` | 21 / 21 | 20 / 20 | 26 / 26 |
| `evidenceDate` | 21 / 19 | 20 / 20 | 26 / 24 |
| `salaryVerifiedAt` | 21 / 13 | 20 / 3 | 26 / 13 |
| `postedAt` | 21 / 1 | 20 / 12 | 26 / 3 |
| `firstSeenAt` | 21 / 0 | 20 / 20 | 26 / 7 |
| `lastSeenAt` | 21 / 0 | 20 / 20 | 26 / 7 |
| `listingStatus` | 21 / 21 | 20 / 20 | 26 / 26 |
| `statusNote` | 21 / 21 | 20 / 20 | 26 / 26 |

Syntactically valid HTTP(S) primary URLs: curated 21/21, automatic 20/20, published 26/26. No URLs were contacted. Published empty/missing evidence dates: `SA-005`, `SA-008`. Source/job IDs are sparser on curated rows; interpret completeness by collection type. `salaryVerifiedAt` can coexist with unknown basis and does not prove verified base pay. Summaries and keyword lists are not original job descriptions.

## Internal consistency and preserved limitations

- Four copied JSON files parse. Each source/copy pair is byte-identical; checksums and byte sizes are recorded. Published schema version is 2. IDs are unique within each population.
- Review categories sum to 30; duplicate (ID, category) pairs: 0; unresolved queue references: 0; overlapping approved/rejected IDs: 0. Stored run review count matches: true.
- Curated IDs missing from published data: 0; published IDs missing from inputs: 0; published source IDs without health entries: 0.
- Retained automatic records: 20; currently `Open in feed`: 14; stored source matched-count total: 15. Retained history includes absent/legacy rows, and source counts are reported before ID-based merging. **Discrepancy preserved:** `workable-robusta` reports two matches but has one retained automatic record (one open). Raw feed responses are unavailable, so the exact reason cannot be established; duplicate normalized IDs are a possible explanation, not a verified observation. Do not use source matched counts as a unique-record evaluation denominator. Missing legacy decisions remain unchanged. Per-source comparisons appear in `observedDiscrepancies` in the manifest.
- 5 automatic records carry review flags with null pay and no queue item: `AUTO-lever-sambatv-1a1da613ae7a`, `AUTO-lever-sambatv-6dd68a1c79e3`, `AUTO-lever-sambatv-6a969d39672e`, `AUTO-lever-sambatv-b11bfeae8d80`, `AUTO-greenhouse-sapience-e9a7dee0a057`. The existing queue builder requires numeric pay for pay-basis entries; flag and queue coverage differ.
- Possible duplicate/geography conflict remains untouched: `SA-004` is Saudi/Jeddah, while `AUTO-workable-robusta-a033b6913e0c` is Egypt/Cairo. Both carry job token `D8EA0BA357` in different URLs. Counts do not establish unique requisitions.
- Stored source status is successful for 6/6 enabled boards. Stored collection/publication is `2026-10-21T10:13:37Z`, later than the approved audit. These are stored statuses, not fresh checks by this capture. Published version `502461042f744e2d` omits some material fields; byte hashes remain authoritative.
- Published JSON deep-matches existing dashboard seed data. HTML is checksummed, not copied. Curated metadata/source-health describe an earlier seed and need not equal generated metadata. Full published/curated FX metadata is retained without independent verification.

## Evaluation integrity and metrics unavailable

| Metric | Status and reason |
| --- | --- |
| Relevance Precision, Recall, F1 | **Not measurable from current snapshot.** No independent labels. Excluded job postings and full historical job descriptions are not retained; historical Recall cannot be reconstructed from retained records alone. |
| Salary eligibility/comparability accuracy | **Not measurable from current snapshot.** Existing flags are not independent labels. Original pay wording, withheld bands, and geographic applicability are incomplete. |
| Evidence correctness / source-supported-answer accuracy | **Not measurable from current snapshot.** Metadata coverage is observable, but immutable source passages and independent support judgments are absent. |
| Review accuracy, resolution rate, review latency | **Not measurable from current snapshot.** Decision arrays are empty; reviewer/reviewed-at/outcome history is absent. A backlog count is observable. |
| Competency Question answer correctness | **Not measurable from current snapshot.** No finalized questions, independent expected answers, or evaluation harness exists. |

Future evaluation requires a fixed corpus containing original descriptions, relevant excluded candidates, original salary evidence, and independently reviewed labels. **Use the exact same fixed corpus and evaluation criteria for Before and After**, including identical treatment of ambiguity, duplicates, manual overrides, and eligibility. Current machine approvals and curated flags must not be reused as independent Ground Truth. Missing historical source material was not reconstructed here.

**Hold FX rates constant** when isolating Knowledge Engineering effects on salary eligibility/comparability. Report effects of changed sources, later evidence, currency assumptions, or collection times separately. Capture timestamp and stored collection timestamp remain distinct.

## Verification boundary

Only local Node built-ins and read-only Git commands were used. Pre-existing production files, tests, workflow, dashboard, data, and the approved audit were hashed before and after capture and remained unchanged. No refresh, collection, build, deployment, dependency installation, commit, pull, push, labeling, taxonomy, ontology, or new classifier was performed. [verify.cjs](verify.cjs) reproduces descriptive calculations and verifies integrity without production refresh. See [MANIFEST.md](MANIFEST.md) for commands and integrity limits.

Stop after Step 0.2 pending review.

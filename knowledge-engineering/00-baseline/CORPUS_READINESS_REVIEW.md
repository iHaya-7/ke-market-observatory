# Stage 0 — Corpus Readiness Review

Review date: 21 October 2026 (Asia/Riyadh). Repository inspected: `945e498` (`Complete Stage 0 Stage 0.3B — Corpus Capture`). Corpus: `20261021T125408Z-ebb0b062`. Approved baseline: `20261021T110236218Z-ec7c36e4`, implementation HEAD `ee5bd15ff52b6a88e15a2dafab6886422980f557`.

**Disposition: original evidence is accessible for all 40 cases, but the evaluation package is not yet ready for unrestricted independent labeling.** Resolve claim specifications, acknowledge salary coverage limitations, review the residual split risk, and resolve the baseline checkout integrity issue before releasing the labeling package. No Ground Truth decisions are made here.

This metadata-only review continues [CORPUS_INVENTORY.md](CORPUS_INVENTORY.md) and [corpus-inventory.json](corpus-inventory.json), using [AS_IS_AUDIT.md](AS_IS_AUDIT.md), [EVALUATION_PROTOCOL.md](EVALUATION_PROTOCOL.md), and the approved snapshot manifest/results. No prior readiness report was present. The 40 selected cases, 10 development / 30 held-out allocation, groups, claims, evidence, and blank review fields remain unchanged. The additional untracked snapshot `20261021T110343966Z-ee5bd15f` was present at entry and is not substituted for the approved reference.

## 1. Evidence completeness

The privately shared `local-corpus/` directory is present. Read-only verification passed for all **83 raw responses, 300 captured posting occurrences, 263 upstream identities, and 40 selected cases**. All **550 artifacts** listed in the corpus seal are present and byte-identical to their sealed hashes. Selected replay inputs match captured originals and detail overlays; source-only CSV references resolve. All human decisions, rationale, review/adjudication metadata, and comparison partners are blank.

All 40 packets contain nonempty original description fields and identifiable responsibility context, beyond a title or normalized summary. Inspection covered the responsibility sections, compensation context, claim fields, and original-record references across every selected case. This establishes availability for independent reading, not a determination that every relevance question is answerable. Ambiguous scope remains for Haya and Lubna to judge independently.

Completeness is relative to the captured API responses. It does not establish that a public website had no additional content, that an upstream field was never omitted, or that postings remain live. No live pages were requested. Some content is HTML or HTML-entity encoded; a reviewer must inspect the complete decoded source, including Lever responsibility lists and additional text, rather than just an introductory field. Any future readable rendering must retain the immutable original and its mapping; none was created here.

Source attribution, original URL, capture time, source/job identity, and artifact hashes are available. Recruiting-agent attribution does not by itself establish an unnamed hiring client's identity. This is an assessment limitation, not missing local evidence.

## 2. Salary evidence readiness

Observable coverage, not eligibility labels:

| Evidence characteristic | Selected cases | Readiness implication |
| --- | ---: | --- |
| Structured salary band | 9 | All are Lever USD annual bands; numeric fields alone do not establish base-pay basis. |
| Structured band plus dedicated prose salary range | 4 | Two ranges agree numerically; two disagree. Preserve both sources of evidence. |
| Structured band without dedicated salary-range prose | 5 | Compensation basis requires independent assessment; do not infer base pay from the structured field name. |
| Sapience prose base-pay range with empty structured pay ranges | 11 | Text includes a dollar symbol and equity separately, but no explicit annual/monthly period or currency code in the description. US location provides context, not an explicit unit declaration. |
| Nearform prose salary range with empty structured pay ranges | 2 | Amounts and bonus/benefits context are present; the salary passage does not explicitly state the pay period. Currency codes in a separate allowance passage must not be attributed automatically to salary. |

The two structured/prose disagreements are `EVAL-1dc856a41d2f7cc2` and `EVAL-439ca061404674c2`. Locators within each existing private packet are `/salaryFields/salaryRange` and `/descriptionFields/salaryDescriptionPlain`; originals are also retained under `/originalRecord`. Bounds differ between the two representations. No conclusion is drawn about which is authoritative or whether the structured amount represents another compensation measure. The other two dedicated prose cases are `EVAL-4847917fd586d111` and `EVAL-582da882867d643d`; numerical agreement alone is not an eligibility label.

Inventory markers remain useful only as discovery aids: 16 cases have literal base wording, 5 have total-compensation wording, 20 match its currency-before-number pattern, and 15 have neither a structured band nor that pattern. These sets overlap. Base and total wording can describe separate components of one package. Currency amounts can describe equipment allowances rather than salary; missing matches do not establish absence of pay.

Market applicability must be tied to the pay passage and posting geography, including regional restrictions and remote locations. General company geography is insufficient. Retain uncertainty about period, currency, basis, applicable band, and recruiter/client attribution separately. No annualization, currency assignment, band selection, or salary label was performed.

The protocol's target of five clearly documented base-pay candidates cannot be certified from lexical counts. Only two of the four dedicated-prose/structured cases have matching bounds; most additional prose ranges lack an explicit period. Whether sufficient definite salary positives and negatives exist remains a human-review outcome. No multi-band structured examples, publisher estimates, or outside-source repost coverage were established by this corpus.

## 3. Duplicate and split-leakage risks

Verification confirms 40 distinct selected source/job identities and 40 selected conservative groups, with **zero existing groups crossing splits**. Original preparation grouped shared IDs, URL matches, same-board normalized titles, and identical long descriptions. This is not proof that all semantic duplicates were identified.

A supplementary text screen compared all 780 selected-case combinations using lowercased five-word shingles after HTML decoding/tag removal. One combination exceeded a descriptive Jaccard threshold of 0.40: `EVAL-78b69dbc5f1ce9b9` (held-out) and `EVAL-859b464d7ec70521` (development), approximately **0.556**. They share source boilerplate, employment conditions, benefits, and salary wording, but their role-specific duties differ. This is a **candidate for identity/related-variant review, not a confirmed duplicate**. The threshold is a screening choice, not a validated duplicate detector; lower similarity does not rule out duplicates.

Haya and Lubna should decide whether these remain independent postings under the existing grouping policy and document the reason. No grouping, split, or sampling change was made. If a correction proves necessary, the current frozen corpus must remain intact and a separately authorized version would be required before performance claims.

Source templates span both splits. Of 30 held-out cases, 17 come from two sources (8 Lever and 9 Sapience). This limits independence and source generalization even without duplicate requisitions. Access to held-out source content for this readiness check must not be used to tune KE rules; later implementation work should use development material only.

## 4. Claim-reference suitability

All 40 claims are literal content from their recorded source fields, and all claim references resolve. These checks establish provenance, **not a Supported Ground Truth label**.

| Observed claim property | Count |
| --- | ---: |
| Claim equals its entire source field | 24 |
| Claim exceeds 3,000 characters | 20 |
| Claim contains HTML markup or encoded markup | 30 |
| Claims sourced from Greenhouse `content` | 19 |
| Claims sourced from dedicated salary prose | 4 |
| Claims sourced from Lever `descriptionPlain` | 6 |
| Claims sourced from Workable `description` | 11 |

All 19 Greenhouse claims are whole content fields. One Workable claim is also a whole description. These combine many assertions and are unsuitable as a single narrowly scoped material claim without an explicit multi-assertion adjudication rule. The six Lever introductory claims describe the company rather than a specific role responsibility or compensation observation. Several shorter Workable claims contain useful responsibility context; others introduce the organization. Suitability must be approved individually, without assigning evidence-support labels now.

CSV `claim_evidence_ref` values point to `evidence.json#/claim`, the derived claim object. Its `sourceField` permits tracing the literal text back to the preserved original, but the reference is not itself a precise original passage span. Description and salary references likewise address containers. Future claim specifications should identify the original artifact, field/JSON pointer, and exact passage boundaries, including contextual pay evidence where needed. A copied assertion alone cannot substitute for its supporting source.

Recommendation for approval: specify one material role or compensation assertion per case and a precise original locator in a separately versioned claim specification. Preserve every current packet/CSV and record old/new definitions, reason, evidence, author/date, and version. Freeze the approved specification identically for both future runs before labeling. No claims were rewritten during this review. Literal-source claim selection also limits evidence-support diversity; do not invent unsupported assertions to obtain negative examples.

## 5. Metric feasibility and sampling limitations

| Metric | Readiness and required condition |
| --- | --- |
| Relevance Precision/Recall/F1 | Original responsibility evidence permits independent review. Reporting still requires at least 20 definite held-out labels and five of each class under the proposed protocol. No class counts are inferred here. |
| Salary eligibility accuracy | Evidence is inspectable, but unit/basis ambiguities and conflicting ranges may reduce the assessable set. Requires at least 10 definite held-out cases and three of each class; show positive/negative and uncertainty counts. Numerous no-pay cases cannot compensate for a positive shortage. |
| Evidence traceability | The 30 held-out cases exceed the proposed count gate of 10, but claims and precise locators need approval. Later coverage concerns citations actually supplied by each system, not these input packets; missing citations remain in the denominator. |
| Review-case detection | Conflicts and ambiguous compensation provide material for independent assessment, without predetermining Yes/No. Requires at least 10 definite held-out cases and three of each class. Score actual queue membership, not internal flags. |
| Salary comparability | No pairs are assigned. Quantitative comparability is not currently measurable. Any later pair specification needs approval and evidence for market, scope, level, basis, and endpoints; fewer than five assessable pairs permits pair reviews only. |

No accuracy metric is presently measurable without independent labels and accounted-for outputs. Zero denominators mean Not measurable. Sampling is small, purposive, machine-stratified, source-concentrated, and prospectively captured in one window. It cannot estimate market prevalence, historical recall, or broad superiority. The inventory's documented allocation shortfall remains unchanged and is not repaired through labels or replacements.

**Expansion decision:** do not expand merely to reach the intended sampling strata. A small, separately approved supplemental corpus is justifiable if Haya and Lubna require coverage of explicit period/base-pay examples, multi-band applicability, or genuine secondary evidence that the current capture cannot supply. Its minimum size cannot be determined before agreeing the coverage objective and assessing the existing evidence; additional cases do not guarantee class balance. Prefer accepting a narrower pilot with explicit metric limitations if expansion is unnecessary. Any supplement would be separately versioned, grouped for leakage, and applied identically to both runs. No collection or case selection was performed here.

## 6. Integrity verification and limitations

The corpus seal SHA-256 matches the published inventory exactly:

`95ccf792916728d6c49a3059a9c053b6021db6c1a48c8c41353bdb295be13e9c`

The existing read-only corpus verifier passed, including raw-response pointers, selected-input equality, blank human fields, references, grouping, and ignored/untracked private artifacts. No local evidence is missing or hash-mismatched.

The approved baseline's standard Node verifier **failed** with `invalid SHA256SUMS line`. Independent read-only inspection found CRLF in the checked-out seal. Four of its eight sealed files (`BASELINE_RESULTS.md`, `MANIFEST.md`, `manifest.json`, `verify.cjs`) differ from sealed bytes; replacing CRLF with LF in memory reproduces their sealed hashes. All four frozen data copies match their sealed hashes byte-for-byte. The seal's current disk hash is `efb3f04022e51959fa4ca49c562ceb9a27b1253ed7258e311ff143458b527a86`; its in-memory LF form and committed seal blob match the inventory's expected `6470fbb886bae2b4885e61d265f658209ad68130a2f88baaaa630325872810c1`.

This is consistent with checkout line-ending conversion, but the current snapshot cannot be described as passing strict byte-integrity verification. No seal or snapshot was repaired or normalized. Haya and Lubna must approve how to establish the exact sealed reference before evaluation; preserve this checkout as found and request the original sealed bundle if necessary.

Existing tracked files, all local corpus files, and both snapshot directories were fingerprinted before report creation and checked afterward. The final comparison found no changed or missing pre-existing files. Git status retains the pre-existing untracked snapshot and adds only this report. Thus unchanged-during-review is verified separately from the pre-existing baseline mismatch. No refresh, network capture, dependency installation, workflow/dashboard change, implementation, commit, pull, push, or deployment occurred.

## 7. Decisions for Haya and Lubna

1. Resolve the baseline checkout/seal discrepancy without modifying the original snapshot during this review.
2. Approve narrow claim definitions and original passage locators, with an explicit versioned amendment that preserves the existing 40 cases and evidence.
3. Review the identified cross-split similarity candidate and document whether existing independent grouping is defensible. Do not silently regroup or move cases.
4. Confirm salary ambiguity handling and the applicable observation/band rule, accepting that some proposed reporting gates may be unmet. Do not resolve missing periods or competing amounts by assumption.
5. Approve the pilot's sampling limitations and either defer supplemental coverage or separately authorize a bounded extension. No expansion is authorized by this report.
6. Confirm the protocol and labeling release: Haya and Lubna independently review source-only materials, calibrate on development cases, freeze the rubric before held-out labeling, and retain both initial judgments plus documented disagreement resolution. Keep machine inventories, sampling strata, and predictions outside reviewer materials. Comparison-pair selection remains deferred.

Stop after this readiness review. Original evidence is available; claim preparation and the listed human decisions remain outstanding before the complete evaluation package is released for labeling.

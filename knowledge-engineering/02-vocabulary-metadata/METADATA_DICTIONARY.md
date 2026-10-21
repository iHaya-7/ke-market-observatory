# Stage 2 — Metadata dictionary

21 October 2026 · Proposal for team review; no schema migration or values created.

Inspected [curated records](../../data/curated.json), [automatic records](../../data/auto_records.json), [published data](../../public/data/market.json), [override lists](../../data/review_decisions.json), [source configuration](../../config/sources.json), [collector](../../scripts/refresh.py) (`normalize`, `salary_info`, `experience_info`, `assemble_records`, `build_review_queue`, `validate_market`), and the public [evaluation-template header](../00-baseline/evaluation-template.csv). No standalone JSON Schema file was found; `schemaVersion: 2` and procedural validators do not provide a complete required-field contract. No private evaluation materials were read.

`R` means a record in curated/published `records[]` or the automatic root array. **E** = exists in production; **T** = existing evaluation-template field only; **P** = proposed knowledge-layer field, not implemented. Grouped names are exact fields sharing a purpose. Missingness describes current evidence/handling, not a new validator. CQ numbers abbreviate CQ-01–06.

## Existing production metadata

| Exact field/path (status) | Business meaning and expected type | Source/provenance | Missing/unknown treatment | CQs |
| --- | --- | --- | --- | --- |
| `schemaVersion` (E) | Dataset format version; integer `2`. | Curated/published envelope. | Required by validator; automatic file is an array without it. | All |
| `R.id` (E) | Record identifier; string, unique within dataset. | Curated ID or hash of source/upstream ID for automatic records. | Required; not a unique-requisition guarantee. | All |
| `R.sourceId`, `R.sourceJobId` (E) | Board link and upstream posting identifier; strings. | Adapter/configuration. | Source ID may be null; upstream ID absent in curated records and some merged rows. Do not fabricate. | 01, 05, 06 |
| `R.company`, `R.title`, `R.family`, `R.exactTitle` (E) | Display company, advertised title, coarse title grouping (strings), exact-title match (boolean). | Curated authoring or config/title rules. | Present in inspected records; company may identify recruiter, not employer. Not authoritative role/identity judgments. | 01, 02 |
| `R.skills` (E) | List of named matched/curated terms; string array. | Regex matches or curation. | Empty array can mean no detected terms, not absence of relevant duties. | 01, 02 |
| `R.relevance`, `R.roleDecision`, `R.roleReviewReason` (E) | Stored category, acceptance state, reason; strings. | Rules/curation; manual role approval may change published decision. | Six legacy automatic rows lack decision/reason. Missing decision defaults to pending in routing, not human uncertainty Ground Truth. | 01, 02, 06 |
| `R.summary`, `R.summaryAr`, `R.notes` (E) | Descriptive prose; strings. | Curation or generated term summary; Arabic summary is curated. | `summaryAr` absent on automatic rows. Summaries cannot replace original duties. | 01, 02, 05 |
| `R.country`, `R.city`, `R.region`, `R.restrictions` (E) | Location/grouping and applicability notes; strings. | ATS mapping/heuristics or curation. | Unknown/empty text possible; no verified pay-market implication. | 03, 04 |
| `R.level`, `R.experience`, `R.levelBasis` (E) | Level, experience wording, explanation; strings. | Title/year rules or curation. | `Not specified` is explicit unknown, not Junior. | 02, 04 |
| `R.expMin`, `R.expMax` (E) | Experience-year bounds; integers or null. | First matching wording or curation. | Null permitted; overall versus specialized years may be unresolved. | 04 |
| `R.salaryMin`, `R.salaryMax` (E) | Numeric salary bounds; finite nonnegative numbers or null. | Structured ATS extraction or curation. | Null allowed; maximum requires minimum and ordered bounds. Missing maximum permits a floor, not an invented ceiling. | 03, 04 |
| `R.currency`, `R.period` (E) | Pay units; string or null. | Adapter/source wording or curation. | Numeric pay requires USD/GBP/EUR/SAR and Annual/Monthly. Missing units cannot be inferred; current parser may withhold the amount. | 03, 04 |
| `R.salaryBasis`, `R.compensation` (E) | Stored basis code and display description; strings. | Parser/curation. | Basis absent on legacy automatic rows. Codes include `base`, `total`, `unknown`, `none`; curated `estimate`/`unverified` mix evidence status into this field. `none` does not universally prove no disclosed pay. | 03, 04 |
| `R.salaryBasisVerified`, `R.salaryEligible` (E) | Stored booleans for recognized basis and base-pay eligibility. | Parser/curation. | Verification flag absent on legacy rows; false/withheld is not independent human ineligibility. Recognized total pay may be “verified” but not base eligible. | 03, 04 |
| `R.evidenceType`, `R.sourceLabel`, `R.evidenceMethod`, `R.collection`, `R.origin` (E) | Evidence category, display label, collection/derivation prose; strings. | Adapter constants or imported curation. | Present but not authoritative attribution; automatic `employer` may describe a recruiter board. | 03, 05 |
| `R.sourceUrl`, `R.extraUrl` (E) | Primary/secondary links; strings. | Canonicalized upstream URLs or curation. | Primary URL required by validation; secondary may be empty. Canonicalization does not prove requisition identity. | 05, 06 |
| `R.evidenceDate` (E) | Recorded evidence date; date string or null. | Automatic collection date or curated research/import value. | Null exists; not necessarily source publication or independent verification date. | 03, 05 |
| `R.salaryVerifiedAt` (E) | Timestamp/date string or null for stored salary evidence processing. | Automatic `now` when numeric minimum retained; curated values imported. | Null allowed. Despite name, not a human-verification timestamp or proof of base pay. | 03, 05 |
| `R.postedAt`, `R.firstSeenAt`, `R.lastSeenAt` (E) | Source-supplied posting date and collector observation timestamps; strings or null. | ATS where supplied; collector clock. | Nulls present; Lever publication is not inferred. Observation time is not source publication time. | 05 |
| `R.listingStatus`, `R.statusNote`, `R.missingChecks` (E) | Listing observation, explanation (strings), successful-absence count (integer). | Collector history/curation. | Count absent on many curated rows; no confirmed vacancy closure inferred. | 05, 06 |
| `R.duplicateGroup` (E) | Curated possible-overlap grouping; string or null. | Curation. | Absent/null permitted; does not resolve unique requisition. | 04, 06 |
| `R.reviewRequired`, `R.reviewReason` (E) | Internal review flag (boolean), reason (string/null). | Salary/role rules or curation. | Reason may be absent/null. Flag is neither queue membership nor human judgment. | 06 |
| `reviewQueue[].id`, `.category`, `.reason`, `.company`, `.title`, `.sourceUrl` (E) | Actual queue item; strings; `id` references a record. | `build_review_queue`. | Queue may be empty; emitted items have these fields. Identity is `(id, category)`; no decision date/history. | 06 |
| `data/review_decisions.json`: `approved`, `rejected` (E) | Lists of record IDs used for role overrides; string arrays. | Manual configuration input. | Empty arrays allowed; not completed independent reviews or salary verification. | 06 |
| `config.sources[]`: `id`, `company`, `type`, `account`, `scope`, `boardUrl`, `enabled` (E) | Board identity/configuration (strings) and enabled boolean. | Maintained configuration. | Configured entries supply these; `scope` is descriptive, not evidence of a posting's relevance. | 01, 05 |
| Dataset `sources[]`: `status`, `error`, `lastAttemptAt`, `lastSuccessAt`, `jobCount`, `matchedCount` (E) | Source health/errors, timestamps, integer counts. | Collection results; shares board configuration fields. | Errors/success times may be null/empty. Feed success/counts are not verified job truth or unique-case denominators. | 05, 06 |
| `fx.rates`, `.date`, `.source`, `.usdSar`, `.usdSarBasis` (E) | Currency-to-SAR numeric map, reference date/source strings, USD/SAR number and assumption string. | FX retrieval and retained curated assumptions. | Comparison needs fixed valid rates; unavailable update can retain earlier rates. Conversion does not establish comparability. | 04 |

`salaryReview` exists only as an intermediate `salary_info` result, removed before record persistence; it is not a production JSON field. Dataset `meta`, `changes`, FX labels/status/attempt/error fields and dashboard presentation details remain operational context, not a complete claim provenance or human-review history. This is a CQ-focused dictionary, not a full API schema.

## Existing evaluation-only metadata

These are **T**, defined by the unchanged template/protocol, not proposed production fields or evidence that labels exist.

| Exact names | Meaning / expected type and provenance | Missing allowed | CQs |
| --- | --- | --- | --- |
| `case_id`, `duplicate_group_id`, `dataset_split`, `source_id`, `source_job_id`, `source_url`, `captured_at_utc`, `original_job_title` | Case/source identity, split, UTC capture, title; CSV strings from preparation. | Case identity required for evaluation; no invented source facts. | All |
| `description_ref`, `salary_evidence_ref`, `claim_text`, `claim_evidence_ref`, `comparison_case_id` | Artifact/passage references, assertion text, optional designated partner; strings. | Unresolved claims/partners remain explicit or blank; never negative labels. | 03–05 |
| `human_relevance`, `human_role_scope`, `human_salary_eligibility`, `human_comparability`, `human_evidence_support`, `human_review_required` | Independent categorical judgments as defined in protocol §1. | Blank means unreviewed; distinct from definite negative and Insufficient Evidence. | 01–06 |
| `human_review_reasons`, `decision_rationale`, `uncertainty_fields` | Reason lists/rationale; CSV strings written by reviewers. | Blank until review; explain unresolved facts. | All |
| `reviewer_id`, `reviewed_at_utc`, `label_status`, `adjudicator_id`, `adjudicated_at_utc`, `label_version` | Reviewer, UTC times, lifecycle/version; strings. | Blank pending review/adjudication; preserve independent initial judgments. | 05, 06 |

## Essential proposed metadata

All names below are **P**, illustrative names for review, not implemented schema paths. They supplement, rather than redefine, current fields. Mandatory identifiers are required only when a corresponding new item is created; unresolved content must remain explicit.

| Proposed field names | Business meaning / expected type | Provenance and missingness | CQs |
| --- | --- | --- | --- |
| `responsibilityId`, `responsibilityText`, `representationMention`, `responsibilityEvidenceRefs` | Bounded duty identifier/text, referenced knowledge/meaning, evidence-reference array. | Original passage plus documented interpretation. Evidence required for a supported assertion; representation may remain unknown. No duty inferred from keywords. | 01, 02 |
| `salaryObservationId`, `salaryEvidenceRefs`, `applicablePayMarket`, `bandApplicability`, `compensationComponents`, `attributionEvidenceRefs` | Observation ID, reference arrays, market/band descriptions, component list. | Separate original structured and prose evidence. Context/components may be unknown; do not overwrite disagreements or fill amounts. Publisher identity does not establish hiring-client identity. | 03, 04 |
| `evidenceId`, `artifactRef`, `artifactSha256`, `capturedAtUtc`, `passageLocator` | Evidence ID; artifact/hash/time strings; locator object defining pointer, span boundaries and text transform when needed. | Capture manifest/original artifact; required for a complete trace chain, otherwise explicitly incomplete. Already specified conceptually for evaluation, not implemented in production. | All |
| `claimId`, `claimVersion`, `claimText`, `claimEvidenceRefs` | Stable assertion/version, bounded text, evidence-reference array. | Approved claim specification or attributable source assertion; text may remain unresolved, never synthesized to fill a gap. | 05 |
| `assessmentOrigin`, `assessmentTarget`, `assessmentOutcome`, `assessmentEvidenceRefs`, `assessmentVersion`, `unresolvedFacts` | Machine/curated/human origin, target and outcome strings, reference array, version, list of unresolved facts. | Recorded rule run or documented human assessment. Origin/target required if recorded; outcome may be unreviewed/undetermined. Reuse protocol review metadata rather than invent parallel Ground Truth labels. | All |
| `identityReviewRefs`, `comparisonContext` | Documented identity-decision references; object for designated observations, dimensions, endpoint and fixed FX reference. | Human-approved decisions/specifications. Null until decided; no pairs or resolved identities assigned now. | 04, 06 |

Team decisions: approve proposed names and mandatory trace requirements; preserve legacy raw values; separate compensation basis from evidence status and publisher from employer; and agree how explicit unknowns and review provenance will later be represented. Do not silently migrate flags into human judgments. An ontology cannot supply absent evidence.

# Stage 0 — Claim specifications v1 review

Prepared 21 October 2026 (Asia/Riyadh) for Haya and Lubna. **Status: proposed; approval pending.** This is source-evidence preparation, not Ground Truth labeling, role classification, or a release for evaluation.

Corpus: `20261021T125408Z-ebb0b062`. References: [EVALUATION_PROTOCOL.md](EVALUATION_PROTOCOL.md), [CORPUS_INVENTORY.md](CORPUS_INVENTORY.md), [CORPUS_READINESS_REVIEW.md](CORPUS_READINESS_REVIEW.md), and the now-approved [BASELINE_INTEGRITY_RESOLUTION.md](BASELINE_INTEGRITY_RESOLUTION.md).

## Completeness and scope

All **40 existing cases** are accounted for with stable IDs of the form `CLAIM-v1-<existing-case-suffix>`. There are **38 proposed claims** and **two unresolved claim selections**. The proposed claims comprise 34 responsibility statements, three compensation statements, and one technical-work requirement. Categories describe assertions, not KE relevance or evidence support.

The 38 excerpts are 50–233 characters long. Each is a contiguous, literal passage from a deterministically normalized reading view of the original source field; none is paraphrased. Selection favored specific responsibilities or technical work over introductions, marketing text, and whole descriptions. A candidate-requirements passage is explicitly identified as such rather than silently converted into an unconditional responsibility. An excerpt states what the posting says; it does not establish that the advertised work or compensation is independently true.

No suitable narrow technical-work or compensation assertion was selected for `EVAL-4bc2915a9cd47faf` and `EVAL-d3e7c52d1ad61855`. Their private entries retain stable claim IDs, null claim text/category/locator, original-source context, and preparation reasons. Haya and Lubna should decide whether a broader operational-responsibility claim is within scope or leave claim selection unresolved. These are not negative relevance or evidence-support labels, and the cases remain in the corpus.

Claim selection used original source passages and the source-only case roster. No case-level predictions, candidate inventory, sampling ledger, or future outputs were opened for this task. Aggregate machine counts were already present in the required inventory and prior conversation context; therefore this is not a claim of complete historical blinding. No case-level machine decisions or sampling strata are included in the new reviewer-facing files.

## Private versioned deliverables

All excerpts, exact source locations, compensation context, and detailed case notes are inside the existing Git-ignored run:

`knowledge-engineering/00-baseline/local-corpus/20261021T125408Z-ebb0b062/claim-specifications-v1/`

| File | Purpose |
| --- | --- |
| `claim-specifications.v1.json` | Forty case entries, proposed claims or unresolved selections, attribution, original locators, context, and amendment notes. |
| `verify_claim_specifications.py` | Read-only structural, provenance, span, privacy, and original-seal checks. |
| `verification.v1.json` | Verification receipt and specification checksum; no accuracy or Ground Truth results. |
| `SHA256SUMS.v1` | Separate seal of the three new version files; does not replace or extend the original corpus seal. |

Specification SHA-256: `dcb28a744f86de191834e07825432cc3bccbbfdea3ecbbda7c1c3fc612e72d90`.

Version-seal SHA-256: `e0daeec93b87cf3bc0efafbebada5f66406185851fc9d41ffc0fcaf63c71dcc6`.

This shareable document contains metadata only. Do not force-add the ignored private directory or copy its excerpts into public review materials.

## Source-reference quality

Every proposed claim records its original parsed artifact and SHA-256, JSON pointer under `/record`, original raw-response artifact and SHA-256, and corresponding raw-response JSON pointer. The referenced values are checked for equality between parsed originals and raw responses. Claim locations do not rely on `evidence.json#/claim`; references to the old claim are retained only as amendment history, with the original packet hash.

Exact spans use zero-based Unicode codepoint offsets, start inclusive and end exclusive, in the declared reading view: parse JSON, apply Python `html.unescape` three times, replace `<[^>]*>` matches with a space, collapse whitespace, then strip outer whitespace. Each locator includes the exact excerpt and hashes of both the original string and normalized string. This makes HTML/entity-heavy passages reproducible without modifying source bytes. These are text offsets, not file-byte offsets or JavaScript UTF-16 offsets.

Neighboring passages retain immediate context with their own exact spans. Title attribution and full original-record references preserve the broader section and role context; reviewers should consult them rather than judge only the short excerpt. Original location fields and source identity remain accessible separately. Reviewer-facing content does not import normalized machine fields.

## Compensation ambiguity

The three compensation claims describe explicit prose statements; they do not assert eligibility, comparability, or the authority of prose over structured data. Structured values and prose references are retained separately, together with geographic/source context, for all cases where those original fields exist.

Both previously identified structured/prose range disagreements remain explicit in private preparation notes. One affects a proposed compensation claim; the other remains context for a responsibility claim. Neither was resolved or converted into a preferred salary observation. Other notes preserve missing explicit pay periods/currency codes, distinguish salary from separate benefits, and caution against inferring base pay from a structured band or identifying an unnamed hiring client from the publishing board.

No periods, currencies, compensation basis, applicable markets, bands, or attribution were filled by assumption. The specification does not designate comparison partners or make salary judgments. Responsibility-claim selection does not remove salary evidence from later independent assessment.

## Verification and preservation

The read-only verifier passed with:

- 40 accounted-for cases and 40 unique stable claim IDs;
- 38 proposed exact claim spans plus 38 neighboring-context spans;
- 344 original-source references checked;
- all 550 original sealed artifacts matching the unchanged corpus seal;
- original human-review and comparison-partner fields still blank;
- no Ground Truth, prediction, or sampling-stratum fields in the specification;
- all new private files ignored and untracked.

Reproduce from the repository root using installed Python; no dependencies or network are needed:

```powershell
python -B knowledge-engineering/00-baseline/local-corpus/20261021T125408Z-ebb0b062/claim-specifications-v1/verify_claim_specifications.py
```

Structural checks establish traceability and literal attribution, not human evidence-support labels. Editorial inspection assessed the proposed excerpts for specificity; Haya and Lubna retain approval of scope and contextual adequacy.

Before/after fingerprints found **all 614 pre-existing files unchanged**, including the original case packets, CSV, raw evidence, snapshots/seals, production files, and prior reports. Only this shareable report and four private version files were added within the repository. The original 40 cases, grouping, splits, and sampling remain intact. No production refresh, collection, comparison pairs, metrics, labels, implementation, commit, or push occurred.

## Approval requirements

Haya and Lubna should approve the 38 proposed claim definitions and locators, resolve the two null claim selections, and confirm the treatment of the candidate-requirement passage and compensation conflicts. Literal source selection does not deliberately introduce unsupported assertions; any resulting limitation on evidence-support diversity must be acknowledged rather than repaired with invented claims.

Upon approval, identify this specification version explicitly for both future runs and future labeling copies. The original CSV and its old claims remain historical artifacts; they must not be silently used as the new claim set. Any revisions should receive a new version and documented reasons while preserving this v1 proposal. No approval or label values have been filled on behalf of either reviewer.

Stop here pending Haya and Lubna's approval. This preparation does not itself resolve the other sampling, duplicate-risk, comparability, or labeling-release decisions in the readiness review.

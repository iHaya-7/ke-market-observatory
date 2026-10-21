# Stage 0 — Closeout and Stage 1 handoff

21 October 2026 · Haya and Lubna · Knowledge Engineering Market Observatory

**Stage 0 preparation: complete. Stage 1 may begin. Ground Truth and final evaluation: pending. Human approval of unresolved claims and duplicate identity: pending.** This closeout defers evaluation decisions to the evaluation phase; it does not silently approve them or change frozen artifacts.

## Completed preparation

- [Current-state audit](AS_IS_AUDIT.md): existing behavior, evidence gaps, and measurement boundaries documented.
- Approved baseline snapshot: `20261021T110236218Z-ec7c36e4`, with frozen data, manifest, descriptive results, and seal.
- [Evaluation protocol](EVALUATION_PROTOCOL.md): review criteria, independent-review process, metrics, and fair-comparison controls documented; no accuracy established.
- [Fixed corpus](CORPUS_INVENTORY.md): 40 cases, with unchanged groups and splits of 10 development / 30 held-out; original evidence remains private and sealed.
- Approved [integrity resolution](BASELINE_INTEGRITY_RESOLUTION.md): tested isolated reconstruction passes the original verifier. The untouched Windows checkout's line-ending mismatch and historical README limitation remain documented.
- [Claim Specifications v1](CLAIM_SPECIFICATIONS_REVIEW.md): 38 proposed claims with precise original-source locators, plus two unresolved selections. Preparation is complete; proposal status is preserved.

## Decisions retained for evaluation

**Claims:** Preserve all 38 proposed claims. `EVAL-4bc2915a9cd47faf` and `EVAL-d3e7c52d1ad61855` remain unresolved for future traceability assessment; retain both job cases. Haya and Lubna must document claim approval or unresolved treatment before scoring. Missing claims must not become invented assertions, negative labels, or silent denominator exclusions.

**Salary:** Retain structured/prose conflicts and uncertainty about period, currency, compensation basis, applicable market/band, and attribution. Do not fill missing facts, infer base pay from structured fields, or transfer currency from unrelated benefits. Eligibility and comparability remain human judgments pending evaluation.

**Potential duplicate:** `EVAL-78b69dbc5f1ce9b9` (held-out) and `EVAL-859b464d7ec70521` (development) require a documented human identity/related-variant decision **before final held-out scoring**. Similarity is not confirmation of duplication. No case, group, or split is changed; any necessary correction requires explicit approval and versioning for identical Before/After use.

The corpus is a small, purposively selected, source-concentrated prospective sample with sampling shortfalls, shared templates, salary coverage gaps, and unresolved claim/identity questions. It cannot establish market prevalence or historical recall. Ground Truth, assessable class counts, and evaluation accuracy do not yet exist; apply the protocol's reporting gates later and report unmet metrics as not measurable.

## Stage 1 boundary and evaluation handoff

Stage 1 may define boundaries, intended uses, and competency questions within the existing frozen scope: job relevance, salary eligibility/comparability, source traceability, and review-case detection. Use **development cases only** where examples are needed. No additional evaluation engineering, corpus expansion, or labeling is required to start Stage 1.

Keep held-out cases, claim excerpts, predictions/errors, and future labels unavailable to implementation tuning. Provide tuning work only development materials, not the full private corpus or v1 claim file. Earlier readiness inspection is not permission to reuse held-out evidence for rule design. This is an operating restriction, not a claim that filesystem access controls were installed. Any later tuning exposure must be documented and cannot support an untouched held-out evaluation claim.

Independent labeling by **Haya and Lubna is deferred to the evaluation phase**, before final Before/After results are calculated. Calibrate on development cases, freeze the rubric and claim treatment, independently review held-out evidence without system predictions, and retain both initial judgments plus documented disagreement resolution. Keep evaluation judgments separate from implementation tuning; use identical approved artifacts and criteria for both runs.

**Starting Stage 1 has no identified blocker.** Pending claim, duplicate, and labeling decisions constrain final evaluation, not scope preparation. This closeout adds documentation only; datasets, snapshots/seals, claims, corpus, splits, production code, and workflows remain unchanged. No labels, collection, ontology artifacts, accuracy calculations, commits, or pushes were produced.

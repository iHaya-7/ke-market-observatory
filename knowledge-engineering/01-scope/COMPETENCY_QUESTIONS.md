# Stage 1 — Competency Questions

21 October 2026 · Six proposals for Haya and Lubna's review · Companion to [SCOPE.md](SCOPE.md).

These natural-language questions define required answers and information, not expected answers for particular jobs. Following the local Ontology Pipeline methodology cited in Scope, they serve as stakeholder requirements and later acceptance-check candidates. They do not create labels, a taxonomy, query code, or new evaluation metrics. A missing answer may reflect missing evidence rather than a modeling failure.

## CQ-01 — Responsibility-based relevance

**Which advertised responsibilities, if any, substantively create, curate, validate, govern, integrate, or use explicit knowledge representations or semantic meaning, and what evidence establishes their role in the work?**

- **Business purpose:** Justify job inclusion using actual responsibilities rather than titles or incidental keywords.
- **Knowledge required:** Original duties and context; actions and their objects; the represented knowledge/meaning; whether the activity is substantive, incidental, or unresolved.
- **Expected answer type:** Responsibility passages with locators, an explained relevance determination or unresolved status under the protocol, and missing facts where needed. No matching passage alone is not proof of irrelevance when the source is incomplete.
- **Existing data / gaps:** `title`, `skills`, `summary`, `relevance`, `roleDecision`, and `roleReviewReason` provide current inputs/outputs. Normalized production records do not retain full original descriptions or action-to-object evidence links; keyword hits do not establish duties. Captured evidence and independent judgments are needed for later assessment.
- **Traceability / potential value:** [Audit](../00-baseline/AS_IS_AUDIT.md) §§3, 6, 8 documents title/regex decisions and missing passages; [Protocol](../00-baseline/EVALUATION_PROTOCOL.md) §1 defines `human_relevance`; [Closeout](../00-baseline/STAGE_0_CLOSEOUT.md), “Stage 1 boundary and evaluation handoff,” restricts examples and tuning. Linking responsibilities to their substantive objects could explain inclusion beyond keyword co-occurrence.

## CQ-02 — Core versus adjacent technical work

**For a job with evidenced KE-related responsibilities, is knowledge/semantic representation the primary work or a substantive part of adjacent technical work, and which responsibilities justify that distinction?**

- **Business purpose:** Distinguish role scope without treating every AI, graph, or metadata mention as the same work.
- **Knowledge required:** Primary duties, purpose of the role, how knowledge representations are built or used, and uncertainty about their centrality.
- **Expected answer type:** Core KE / Adjacent technical / Neither / Insufficient Evidence, with passages and rationale following `human_role_scope`. Relevant work may still have unresolved scope; neither category is inferred from a vendor or title alone.
- **Existing data / gaps:** `family`, `relevance`, `skills`, and `levelBasis` exist, but current machine categories are not equivalent to human role scope. Explicit primary-duty and substantive-use evidence may be absent or ambiguous.
- **Traceability / potential value:** Audit §§3, 5 identifies inconsistent category meanings; Protocol §1 separates relevance from scope; Closeout retains pending Ground Truth and development-only design. Explicit distinctions between primary and supporting work could make scope decisions consistent and explainable without imposing a new taxonomy now.

## CQ-03 — Salary evidence and base-pay eligibility

**Does an attributable salary observation support use as employer base pay under the agreed policy, and which evidence or unresolved facts determine that answer?**

- **Business purpose:** Avoid treating an available number or parser flag as verified base-pay evidence.
- **Knowledge required:** Original numeric bounds, currency, Annual/Monthly period, compensation components, applicable market/band, employer or recruiting-agent attribution, structured/prose correspondence, and source context.
- **Expected answer type:** Eligible / Ineligible / Insufficient Evidence with observation references, reasons, and contradictions under `human_salary_eligibility`; separate from job relevance and global benchmark admission. A missing ceiling permits a floor observation under the protocol.
- **Existing data / gaps:** `salaryMin`, `salaryMax`, `currency`, `period`, `salaryBasis`, `salaryBasisVerified`, `salaryEligible`, `evidenceType`, `country`, and salary evidence dates exist. Flags are not human verification. Free-text amounts, withheld bands, explicit units/basis, and attribution can be incomplete or conflicting.
- **Traceability / potential value:** Audit §§4, 6 documents parser limits and misleading verification implications; Protocol §1 specifies supported units and eligibility; Closeout “Salary” preserves ambiguity. Representing an observation separately from its evidence and interpretation could expose unsupported assumptions. Retain USD/GBP/EUR/SAR and Annual/Monthly policy; do not silently broaden it.

## CQ-04 — Salary comparability

**For two explicitly designated salary observations, do their evidenced market, role scope, career level, pay measure, and comparison endpoints permit a like-for-like comparison under the agreed policy?**

- **Business purpose:** Prevent currency-normalized numbers from being presented as substantively comparable pay.
- **Knowledge required:** CQ-03 eligibility for both observations; same country/pay market and gross base-pay measure; materially similar role scope; same explicitly evidenced career level; attribution, band applicability, floor/ceiling choice, and frozen FX/period conversion.
- **Expected answer type:** Comparable / Not comparable / Insufficient Evidence with dimension-by-dimension reasons for an assigned pair; Not applicable when unpaired. Floors are the protocol default; full ranges require two ceilings and a declared endpoint policy.
- **Existing data / gaps:** Salary fields, `country`, `region`, `level`, `expMin`, `expMax`, `levelBasis`, and `fx` supply partial context. Title-derived level and conversion alone are insufficient. Fixed pairs and independently established comparability facts remain pending.
- **Traceability / potential value:** Audit §§3–4, 8 documents experience heuristics and benchmark conversion; Protocol §§1–2, 4–5 defines comparisons and explicitly notes no baseline comparability classifier; Closeout defers evaluation decisions. Explicit conditions could reveal the exact mismatch or missing fact. This CQ does not assign pairs or authorize a new scoring interface.

## CQ-05 — Claim evidence

**Which preserved original source passage supports or contradicts a specified claim, with what attribution and context, and can the evidence chain be resolved?**

- **Business purpose:** Let reviewers inspect the basis of a claim rather than rely on a URL or a summary.
- **Knowledge required:** Fixed claim/version, original source/job identity, capture date, artifact checksum, exact pointer/span, contextual passages, and relevant conflicting evidence.
- **Expected answer type:** A resolvable evidence chain and a separately explained support assessment or unresolved state under `human_evidence_support`. Linkage completeness and claim correctness are distinct; an unresolved claim definition must be reported explicitly.
- **Existing data / gaps:** `sourceUrl`, `sourceId`, `sourceJobId`, `evidenceDate`, `evidenceMethod`, and `origin` provide partial provenance. Production metadata alone lacks immutable passage-level support. Claim approvals and two unresolved selections remain pending per Closeout; no claim specifications were inspected here.
- **Traceability / potential value:** Audit §6 identifies provenance/version limitations; Protocol §§1, 3–4 separates support from traceability coverage; Closeout “Claims” preserves unresolved selections and cases. Explicit claim-to-passage links could enable auditable explanations. Later system outputs receive credit only for citations actually supplied, not evidence links fabricated by an evaluation wrapper.

## CQ-06 — Review needs and reasons

**Which records require human review because a scoped decision depends on unresolved or conflicting evidence, and what specific issue must the reviewer resolve?**

- **Business purpose:** Direct review effort to material uncertainty and expose missed review needs.
- **Knowledge required:** Affected relevance, pay, comparability, or traceability decision; missing facts or conflicts; possible identity overlap; evidence references; internal flags, actual queue membership, and later human review history as separate facts.
- **Expected answer type:** Records with Yes / No / Insufficient Evidence review-need assessments, scoped reasons, and the question to resolve. Compare actual queue membership separately; queue disappearance does not prove resolution.
- **Existing data / gaps:** `reviewRequired`, `reviewReason`, `reviewQueue`, `roleDecision`, and manual approved/rejected IDs exist. Review flags can fail to yield queue entries; decision history lacks reviewer/time/rationale. Review labels and the outstanding duplicate-identity decision remain pending.
- **Traceability / potential value:** Audit §§4, 6, 8 documents routing and history gaps; Protocol §§1, 4 defines review need and actual-queue scoring; Closeout “Potential duplicate” requires human resolution before held-out scoring. Linking reasons to decisions and evidence could make omissions visible without automatically adjudicating them.

## Review and acceptance boundary

Haya and Lubna should confirm that these six questions serve the Observatory's decisions, that the answer forms retain uncertainty, and that exclusions in Scope are appropriate. Later modeling choices should trace to a CQ; later acceptance checks need approved evidence and independently judged answers. No expected case answers, accuracy claims, or evaluation-interface changes are established here. Preserve the frozen artifacts; use development examples only if subsequently needed. Final labeling and disagreement resolution remain in the evaluation phase.

# Stage 2 — CQ coverage and essential gaps

21 October 2026 · Proposal for Haya and Lubna; no implementation or evaluation results.

This maps the six [Stage 1 questions](../01-scope/COMPETENCY_QUESTIONS.md) to the [working vocabulary](VOCABULARY.md) and [metadata dictionary](METADATA_DICTIONARY.md). “Existing” means a field or procedural behavior was inspected, not that its values have been independently validated.

| CQ | Vocabulary needed | Existing metadata foundation | Essential missing distinction/evidence | Potential semantic value |
| --- | --- | --- | --- | --- |
| CQ-01: substantive responsibilities | Job Posting, Job Role, Responsibility, Knowledge Representation, Evidence, Assessment | Title, skills, summaries, relevance/decision and reasons. | Original duty passages linked to actions and represented meaning; explicit assessment origin and unresolved facts. | Explain why duties substantiate relevance rather than merely matching a title or word. |
| CQ-02: core/adjacent scope | Job Role, Responsibility, Knowledge Representation, Assessment | Family/relevance strings and role reasons. | Evidence that representation work is primary or substantively supports adjacent work; human scope is not equivalent to current machine categories. | Make the basis for scope inspectable without prematurely constructing a taxonomy. |
| CQ-03: salary eligibility | Salary Observation, Compensation Basis, Pay Market, Source, Evidence, Assessment | Salary bounds/units/basis flags, location, evidence type/date, source links. | Distinct observation and evidence references; structured/prose contradictions; applicable band and employer/agent attribution. Missing units stay missing. | Separate the advertised measure from extraction and eligibility judgments; expose assumptions. |
| CQ-04: comparability | Salary Observation, Compensation Basis, Career Level, Pay Market, Job Role, Requisition, Assessment | Salary units, FX, country/region, level/years/basis, possible duplicate group. | Evidence of level, market and gross-base measure; designated pair/endpoint context; unresolved identity decision. No baseline comparability classifier exists. | Explain dimensions of a match, mismatch, or uncertainty rather than treating conversion as comparability. |
| CQ-05: claim support | Claim, Evidence, Source, Assessment, Human Review | URLs/source IDs, evidence dates/methods/origin; template claim/reference fields. | Production claim/version-to-original-artifact/passage chain and separate support judgment; capture date is not verification date. | Enable reproducible navigation to evidence, without equating linkage with correctness. |
| CQ-06: review reasons | Review Need, Review Queue Entry, Human Review, Assessment, Evidence, Requisition | Internal flags/reasons, actual queue items, manual override ID arrays. | Affected decision and missing/conflicting facts linked to evidence; reviewer/rationale/version history; explicit separation of need, routing, and resolution. | Expose missed routing and explain review requests; do not auto-adjudicate uncertainty. |

## Evidence and methodological limits

The [audit](../00-baseline/AS_IS_AUDIT.md) §§3–6 and 8 supplies the procedural limitations behind this mapping. The [evaluation protocol](../00-baseline/EVALUATION_PROTOCOL.md) §§1, 3–5 supplies separate judgment dimensions, review metadata, actual-queue scoring, and fair-comparison requirements. Production inspection confirms that structured metadata already exists: the gap is often interpretation and evidence linkage rather than a missing scalar field.

The public protocol and [closeout](../00-baseline/STAGE_0_CLOSEOUT.md) describe preserved evaluation evidence and claim preparation; those private artifacts were not inspected or reused for design. Thus a production gap does not imply that evaluation preparation lacks every corresponding field. The proposed metadata names are a future design contract, not a claim that artifacts have been migrated or missing facts recovered.

No new concept is justified solely to mirror every JSON field. Currency, period, dates, identifiers, numeric amounts, flags, and category values remain metadata at this stage. Skill synonym expansion, occupation hierarchies, ontology classes/properties, RDF mappings, automatic inference, and graph storage are deferred. The learning methodology calls for controlled meaning and CQ-driven scope, not maximal vocabulary size.

## Approval and handoff

Haya and Lubna should approve:

1. The 16 preferred terms, limited alternatives, and separations among posting/requisition, observation/evidence, base/total/OTE, and machine/human assessments.
2. The minimal proposed evidence, observation, responsibility, and assessment metadata; required trace fields and explicit unknown handling; separation of compensation basis from legacy evidence-status codes.
3. Attribution and comparison-context requirements without changing the protocol, assigning pairs, or introducing a comparability scoring interface.
4. Stage 1 scope/CQs and this Stage 2 proposal before later modeling; technical review or preparation alone is not team approval.

Existing fields and frozen artifacts remain unchanged. The two unresolved claims, duplicate identity decision, independent human labeling, and final evaluation remain pending as recorded in Closeout. Held-out cases, labels, predictions, and private claim specifications must remain unavailable for tuning. No case-level examples were needed. Metadata can make uncertainty visible; it cannot resolve missing evidence or guarantee improved accuracy. Stop at these three documents.

# Stage 1 — Scope

21 October 2026 · Proposed for review by Haya and Lubna · No modeling or implementation authorized by this document.

## Scope statement

**This system exists to answer questions about Knowledge Engineering job responsibilities, salary observations and their comparability, supporting source evidence, and human review needs, from the perspective of Observatory analysts and evidence reviewers, for the purpose of making explainable role-inclusion and salary-use decisions while preserving uncertainty and source traceability.**

The proposed knowledge layer is bounded by the six [Competency Questions](COMPETENCY_QUESTIONS.md). It describes information requirements, not ontology classes or a replacement classifier.

## What the knowledge layer will represent

| Area | Required distinctions |
| --- | --- |
| Advertised work | Posting identity, stated responsibilities, the knowledge representations involved, and whether that work is primary or substantively used in adjacent technical work. Titles and keyword mentions are evidence inputs, not proof of responsibilities. |
| Compensation | Salary observations with original amounts, currency, period, base/total/other basis, applicable market/band, publisher/employer or recruiting-agent attribution, and evidence date. Preserve structured and prose evidence separately, including contradictions and missing facts. |
| Comparison context | Role scope, explicitly evidenced career level, market, pay measure, endpoints, and fixed conversion assumptions. Intrinsic salary eligibility, pair comparability, and admission to the existing global benchmark are separate decisions. |
| Evidence | A claim's link to an attributable original artifact, capture time, checksum, precise passage, and necessary context. Distinguish source statements, machine outputs, and independently reviewed judgments. |
| Review | The scoped decision affected by uncertainty or conflict, its reasons and source references, and any later documented human judgment. Review need is distinct from an internal flag, actual queue membership, or a resolved decision. |

Coverage remains the existing Observatory's captured job/source records, including Saudi and non-Saudi observations. No extension to the whole labor market is implied. A posting, salary observation, and possible duplicate requisition must not be assumed to be interchangeable. Unknown evidence remains unknown; proposed relationships do not manufacture missing facts.

## System boundary and exclusions

Existing collection adapters, refresh scheduling, storage, validation, FX retrieval, publication gates, dashboard filters/charts, and deployment retain their present responsibilities. The knowledge layer would make decision meanings and evidence relationships explicit; it does not collect sources, redesign presentation, or change those functions in Stage 1.

Excluded: candidate ranking or hiring recommendations; exhaustive occupation/skill classification; market-wide salary estimates or demand forecasting; inferred pay periods, missing salary amounts, or career levels; tax, purchasing-power, inflation, or hourly-pay normalization; live vacancy verification as a separate task; automated resolution of disputed duplicates or human disagreements; new sources or corpus expansion. Historical/open status matters only when an actual scoped claim depends on it. Vocabulary, taxonomy, ontology, knowledge graph, RDF, inference rules, and query implementation belong to later stages.

## Method, value, and controls

Method follows the accessible local [Ontology Pipeline learning text](../../../Ontology-Pipeline/Ontology-Pipeline.md), sections “Define purpose and scope” (text lines 740–745) and “Competency questions: The ontology’s contract” (5127–5170): identify stakeholder decisions, state exclusions, agree natural-language questions, and justify later modeling through those questions. This sibling learning reference is local, not bundled with the repository. No formalism is selected here.

Potential value is consistent, inspectable explanations: what work supports inclusion, why pay can or cannot be compared, which passage supports a statement, and which missing fact requires review. Explicit relationships could reduce inconsistent interpretation across procedural checks; improved classification or salary accuracy is a hypothesis requiring later evaluation, not an automatic benefit of ontology use.

The [Stage 0 closeout](../00-baseline/STAGE_0_CLOSEOUT.md) remains controlling: frozen baseline/corpus/splits and 38 proposed claims remain unchanged; two claim selections and duplicate identity await human decisions. No case evidence, labels, predictions, or claim specifications were opened for Stage 1; no concrete case examples were needed. Future design examples must use development material only. Keep held-out material unavailable for tuning. Haya and Lubna's independent labeling and documented disagreement resolution remain deferred to evaluation, before final Before/After results.

## Decisions requested

Haya and Lubna should approve the analyst/reviewer perspective, boundaries and exclusions, six CQ answer requirements, and continued use of the evaluation protocol's relevance and salary criteria. Approval of Stage 1 must not be read as approval of pending claims, duplicate identity, Ground Truth, or a new comparability classifier. Any scope or evaluation-interface change needs an explicit, versioned decision before scoring.

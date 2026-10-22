# Stage 7A — Development decision pilot and evaluation readiness

Executed 22 October 2026. Stages 0–6 are technically reviewed; this does not create independent human labels or final semantic approval. The implemented contribution is **evidence-aware salary triage and explicit review routing**. A defensible relevance or salary-eligibility classifier is not yet supported by the existing graph. No accuracy, improvement, or review-workload reduction is established.

## Scope and execution

The pilot uses only the existing **three Stage 5 Development cases**, their three allowlisted preserved artifacts, three selected duties and four salary statements. It does not expand to the other seven Development cases or access Held-out records, labels, predictions, shared raw responses, evaluation CSVs or private claim specifications. Source files, schemas, Stage 5/6 outputs, production and frozen baseline remain unchanged.

Reviewed: the approved Stage 0 baseline manifest/descriptive results, integrity-resolution document and [evaluation protocol](../00-baseline/EVALUATION_PROTOCOL.md); Stage 1 CQs; Stage 2 vocabulary/metadata; Stage 3 SKOS; Stage 4 ontology; Stage 5 graph, builder and documentation; Stage 6 validation code, shapes and report. Baseline snapshot counts are historical descriptive outputs, not predictions for these three cases. No baseline replay was executed in Stage 7A.

Run from the repository root using the already installed Stage 6 local dependencies:

```powershell
python knowledge-engineering/07-evaluation/ke_decision_pilot.py
```

No new dependency or framework is required. The script reuses Stage 6 SHACL and source-integrity checks and the unchanged ontology/taxonomy. It fails without issuing decisions if input structural or integrity checks fail; an execution failure is not a negative decision. It requires the exact existing Development allowlist and never builds or modifies the input graph. SHACL conformance and exact extraction fidelity are prerequisites for reliable navigation, not semantic judgments.

Private output directory: `knowledge-engineering/00-baseline/local-corpus/development/stage7a/`.

- `pilot-results.json`: original represented values, separate candidate interpretations, machine diagnostics/decisions, rules, review questions, actual local pilot queue, evidence trace chains, input/code hashes and checks.
- `pilot-assessments.ttl`: new machine assessments, run/software provenance and local pilot review entries only. Targets and evidence reference the unchanged Stage 5 graph. Load both files' RDF graphs together for navigation; this output is not a replacement source graph.

Each run receives a fresh UUID activity and run-specific assessment/queue IRIs. The files are current output snapshots; reruns replace these pilot outputs only. Domain IRIs remain unchanged. Given identical inputs/code, facts, candidate interpretations, decisions and routing are deterministic; run IDs, record IRIs and timestamps vary. Detailed outputs and excerpts stay Git-ignored. The tracked deliverables are just this document and the script.

## Decision contract, version Stage7A-v1

Four layers remain distinct:

1. **Source facts as represented:** existing duty text and salary scalar values with original observation identities and passage/context references. These are not independently established truths; Stage 5's mapping selected the passages and facts.
2. **Candidate semantic interpretation:** reciprocal source-context links identify statements worth reconciling. This does not establish same-band identity, eligibility or occupational meaning. No relevance interpretation or SKOS assignment is invented.
3. **Machine decision:** rule-identified diagnostics, abstentions and review-need assessments with citations, reasons and provenance. Missing fields refer to the graph/selected statement, not proof of source omission. Machine `Abstain` is not the human `Insufficient Evidence` label: a reviewer may find enough information in the complete source.
4. **Human Ground Truth:** absent from inputs and outputs. It must be produced independently under the unchanged protocol; neither these machine results nor source-fidelity assessments are reference labels.

| Rule | Implemented behavior | Boundary |
| --- | --- | --- |
| R0: relevance boundary | Cite selected duties/context and abstain. Ask whether full advertised work substantively acts on explicit knowledge representations. | No positive or negative relevance rule is implemented. Titles are not read by decision logic. The graph has no substantiated action-to-representation interpretation and does not represent all duties as assertions. Neither keywords nor absence of a relation can decide inclusion/exclusion. |
| S1: statement sufficiency | Inventory lower bound, currency, period, basis and market per observation, plus employer/recruiting-agent attribution. List missing dimensions and multiple differing represented values. | A ceiling is optional. An absent predicate is a graph coverage gap, not source non-disclosure, ineligibility or zero. Publisher identity does not substitute for employer/agent attribution. This inventory is necessary context, not a sufficient eligibility test. |
| S2: contextual reconciliation candidate | Compare only statements belonging to the same posting with reciprocal evidence-context links in the same artifact. Report explicit endpoint agreement, fields supplied across statements and potential disagreement. | No observation merge, transfer of currency/basis/market, pooling, band selection, or comparison pair. Matching endpoints do not prove same-band applicability. Recognized explicit Annual/Monthly and base-pay spellings may be compared; absent values are never supplied. Other lexical differences remain potential disagreements for review, not proven contradictions. |
| S3: salary semantic boundary | Abstain on eligibility even if represented fields are present. Cite each statement and context. | Attribution, interpretation and applicability need review. No inferred units, gross/net measure, experience, base-pay verdict or benchmark admission. This is not an eligibility classifier disguised as completeness checking. |
| V1: human-review routing | For unresolved relevance/pay decisions, emit machine review need `Yes`, concrete questions and local pilot queue entries in `Role relevance` and `Pay evidence`. | A review request reflects this pilot's limitations and evidence gaps; it is not an independent human judgment. The queue is a real written **pilot output**, separate from the untouched production queue and from completed human review. |

The pilot can therefore decide what its represented evidence cannot support for automated use, where contextual reconciliation is needed, and which issues to route for review. It cannot honestly decide Relevant/Not relevant or Eligible/Ineligible. On this subset, requesting review for every case is conservative and non-discriminating; it may over-route cases whose full source permits clear decisions. Review precision and usefulness remain untested.

## Actual execution and verification

| Output | Observed count |
| --- | ---: |
| Development cases | 3 |
| Salary statements | 4 |
| Statements with at least one required represented-field gap | 4 |
| Relevance abstentions | 3 |
| Salary-eligibility abstentions | 4 |
| Machine review-need `Yes` decisions | 3 |
| Total new machine assessments | 10 |
| Local pilot queue items / distinct queued cases | 6 / 3 |
| Contextual statement-reconciliation candidates | 1 |
| Candidates with detected explicit contextual disagreements | 0 |
| Distinct cited passages with supplied trace chains | 10 |

Across the four statements, currency is unrepresented on 3, period on 2, market on 3, basis on 1, and employer/agent attribution on 4. These are overlapping **graph field-gap counts**, not source-quality or eligibility labels. The one contextual candidate supplies the five scalar dimensions across its two separate statements, but attribution and same-band applicability remain unverified; nothing is filled into either observation. Zero detected contextual conflicts is limited to the implemented comparisons, not proof that the full sources are consistent.

Input SHACL and separate source-integrity checks passed: three artifact checksums and ten passage resolutions/text matches. The combined source graph plus pilot assessments also passes the existing shapes. All emitted ontology terms are declared; the pilot RDF parses and round-trips. Hashes verify that input graph, mapping, schemas, protocol, validation code and the three original artifacts remained unchanged during execution.

Five synthetic in-memory controls passed: changing titles does not change decisions; removing units never infers them; an introduced contextual period disagreement is flagged; removing context links prevents the comparison; no unsupported relevance/eligibility verdict is emitted. Synthetic mutations are not saved as evidence or used as accuracy cases. These tests verify procedure behavior, not semantic correctness. Repeat execution preserves case content, diagnostics and decisions while using fresh run identities.

The incremental capability demonstrated is explicit, observation-scoped explanations and cited review requests, including a distinction between genuinely unrepresented fields and complementary contextual statements awaiting reconciliation. These are inspectable operational outputs, **not a measured improvement over the frozen system**. The pilot inherits manually selected Stage 5 evidence and mappings; their preparation effort and semantic selection must be disclosed as part of the KE intervention. Any later benefit cannot be attributed to RDF or rule reasoning alone.

## Fair comparison contract and unresolved dependencies

Use baseline snapshot `20261021T110236218Z-ec7c36e4` and implementation HEAD `ee5bd15ff52b6a88e15a2dafab6886422980f557`. Before any comparison, recover/verify the frozen implementation and seal using the approved isolated reconstruction procedure. The untouched Windows checkout's known line-ending mismatch must not be silently repaired or reported as a direct verifier pass. Stage 7A reviewed that boundary; it did not rerun baseline verification or recreate historical predictions.

Replay the frozen system offline on exactly the same designated cases and original captured inputs, with unchanged adapters, initial state, source settings, override policy, clock, error behavior and output definitions. Do not run collectors. Preserve every case including baseline exclusions, absent fields and abstentions. Use raw baseline outcomes from `assess_role()`, intrinsic `salary_info()` and the actual baseline queue builder; do not manufacture baseline evidence citations or queue entries in an evaluation wrapper. Record both implementation/input hashes and machine outputs separately from reviewer files.

The current pilot consumes a narrower, manually mapped graph derived from those sources. A future comparison must freeze and identify that mapping as part of After, verify that both runs refer to the same captures, and report this input-representation difference. A baseline snapshot's old published records are not a fair comparator for these prospective cases. No baseline outcome is asserted here.

| Indicator | Precise future comparison | Present readiness |
| --- | --- | --- |
| Relevance automatic acceptance | Baseline `approved` is positive; `pending`/`excluded` are non-acceptance. For After, only an explicitly supported Relevant decision could be acceptance; current `Abstain` is non-acceptance, retained separately. On the same independently definite human labels, compute protocol TP/FP/FN and precision/recall/F1 where denominators exist. An abstention on a human positive remains a false negative for acceptance. | No human references and no affirmative relevance rule. No current performance calculation; precision would have no positive-prediction denominator. Human Insufficient Evidence and unreviewed cases remain accounted for outside binary scoring. |
| Salary eligibility | Compare the baseline's intrinsic eligibility independently of role inclusion with After on the **same predesignated observation/band** per case. Current After abstention means no automatic admission, not human Ineligible. | Four graph statements must not become four independent evaluation cases. Haya/Lubna must confirm the protocol's existing band designation or unresolved treatment before scoring; this pilot selects no favorable band and synthesizes no case-level salary label. |
| Evidence traceability | Count only citations actually emitted by each system, resolving through the same preserved identity map. Protocol claim coverage uses fixed approved claims and the unchanged denominator; linkage and semantic support are separate outcomes. | Ten passages are emitted/resolvable here. This is not the protocol's claim-level coverage: private claims were not opened, approved or created. No baseline citation gap is retroactively repaired. |
| Review-need capture | Compare actual queue membership against independent Yes/No review-need labels; report TP/FP/FN, precision/recall/F1 and abstentions/errors under the protocol. Keep flags separate. | The pilot writes six local entries, covering three cases. Haya/Lubna must confirm this offline After queue interface and category crosswalk before a paired comparison; it is not deployed routing. All-case routing could improve apparent recall at the expense of precision. No capture/precision claim yet. |
| Salary comparability | Only already designated pairs, member eligibility, policy dimensions and declared endpoints may be evaluated. | Unsupported; no pairs created or inspected. S2 compares statements within one posting, not salaries across jobs. |

Retain USD/GBP/EUR/SAR and Annual/Monthly policy, optional ceiling, source attribution and applicability requirements. No conversion is performed here. If later needed, use the frozen 2026-10-20 SAR rates: SAR 1, USD 3.75, GBP 5.005005, EUR 4.205639, unchanged period conversion/rounding. Conversion does not establish comparability. No new normalization or salary policy is introduced.

These three deliberately selected Development cases are for calibration and error analysis, not untouched-test evidence or market estimates. The existing reporting gates still apply: relevance needs at least 20 assessable Held-out cases with five per class; salary/review need at least 10 with three per class; claim traceability needs at least 10 Held-out cases. Fewer than five assessable pairs permits pair reviews only. No final accuracy or improvement is measurable now, and no Held-out evaluation is authorized or implemented by this deliverable.

## Precise next step for Haya and Lubna

1. Review this limited decision/output contract, especially graph-coverage versus source insufficiency, conservative all-case review routing, the contextual same-band question, the manually mapped inputs, and the proposed offline queue comparison. Technical review of Stages 0–6 does not settle these semantic/evaluation choices.
2. For the same three Development cases, independently read the **complete preserved original case-specific descriptions and compensation context**, not just the selected graph duties. Use separate, versioned copies of the unchanged evaluation template in an ignored labeling area. A source-only packet should exclude Stage 5 claim candidates, machine assessments, this pilot's review questions/results, baseline predictions and sampling strata. Do not overwrite the frozen corpus/template.
3. Record each reviewer's relevance, role scope, salary eligibility and review-need judgments using the protocol's exact human labels, with evidence locators, uncertainty fields, rationale, reviewer/time and version. Confirm the preselected salary observation/band without changing the evaluation unit. Do not mark unresolved evidence as negative. No pair means no comparability experiment. Claim support remains pending until the separately governed fixed claim is approved; do not label one invented from this pilot.
4. Preserve both independent judgments, then reconcile disagreements with documented rationale and adjudication. Development calibration is separate from final Held-out labeling. Reviewers who have already seen machine outputs should record that exposure; do not describe such judgments as blinded.
5. Compare these calibrated judgments with the frozen-system replay and frozen pilot outputs for Development error analysis only. Freeze any revised extraction/semantic rules, mapping, output interface, rubric and claim treatment before separately authorized final evaluation. Keep Held-out material inaccessible to implementation tuning. Do not transfer Development machine decisions or adjudicated answers into Held-out rules as case-specific lookup labels.

No human labels, labeling files or evaluation metrics were created in Stage 7A. The next dependency is independent Development interpretation, not further infrastructure. CQ-01/CQ-02 relevance and scope, CQ-03 eligibility, CQ-04 comparisons and CQ-05 semantic claim support remain unanswered; CQ-06 now has explicit **machine** review requests, whose correctness remains unjudged. Work stops at Stage 7A with production, frozen artifacts, ontology and SHACL unchanged; no commit or push.

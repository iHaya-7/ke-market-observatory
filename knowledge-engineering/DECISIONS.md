# Modeling Decision Template

- Decision ID:
- Date:
- Status:
- Topic:
- Context and supporting evidence:
- Options considered:
- Decision:
- Rationale:
- Consequences and limitations:
- Related artifacts:
- Reviewer:
- Revisit criteria:

## D-005 — Carry Stage 4 semantics into the Stage 5 MVP

- Date: 2026-10-22
- Status: Implemented for the authorized MVP using technically reviewed working models; final Haya/Lubna approval pending. Technical structural review is not semantic team approval.
- Topic: Minimal ABox, evidence boundaries, and unchanged schema semantics.
- Context and supporting evidence: Stage 1 Scope/CQs, Stage 2 vocabulary/metadata, Stage 3 taxonomy, Stage 4 ontology/CQ traceability, and Stage 0 closeout/evaluation boundaries were reviewed. See [Stage 5 implementation](05-knowledge-graph/GRAPH.md).
- Options considered: Populate every schema class versus instantiate only evidenced records; derive labels from titles versus preserve source duties and leave occupational assignments unresolved.
- Decision: Retain the existing ontology and taxonomy files and IRIs unchanged. Separate postings from requisitions, advertised roles from SKOS concepts, duties from qualifications, salary observations from evidence, and machine assessments from human judgments. Use `roleConcept` only for evidence-backed occupational interpretations; SKOS hierarchy is not OWL subclassing or an inference rule. Similar postings are never merged automatically.
- Rationale: Stage 4 domains/ranges express meaning, not completeness validation. Missing properties remain unknown under open-world interpretation. An evidence link establishes navigation, not truth or support. Salary basis, currency, period, market, career level, eligibility, comparability, and benchmark admission remain distinct; none is inferred from a title, dollar sign, location, parser flag, or missing value.
- Consequences and limitations: Three fixed Development cases only; separate structured/prose compensation observations and contextual passages. Stable instance URNs use original source/job identity and local component keys; artifacts use byte hashes. Original case-specific capture timestamps are retained. New machine assessments check source extraction fidelity only, with software/run/version/criteria provenance; they create no Ground Truth or semantic eligibility decisions. No private claim specifications, Held-out evidence/predictions/labels, automatic pairs, identity adjudication, or review queue entries are used. Review need, internal flag, queue membership, and completed human review remain separate. No SHACL, reasoning, evaluation metrics, or accuracy-improvement claim.
- Related artifacts: [Ontology](04-ontology/ONTOLOGY.md), [CQ traceability](04-ontology/CQ_TRACEABILITY.md), [Taxonomy](03-taxonomy/TAXONOMY.md), [Stage 0 closeout](00-baseline/STAGE_0_CLOSEOUT.md).
- Reviewer: Haya and Lubna — final review pending; no approval recorded on their behalf.
- Revisit criteria: Team semantic approval, authorized new evidence or concept assignments, or an explicitly versioned change to meanings/identifiers. Evaluation decisions remain deferred.

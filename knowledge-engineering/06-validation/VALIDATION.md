# Stage 6 — Lightweight SHACL validation

Executed 22 October 2026. **Ready for technical approval:** the existing three-case Development graph conforms, all intended negative controls are detected, and separate local source-integrity checks pass. This is not team semantic approval, Ground Truth, or evidence of improved classification accuracy.

## Implementation and reproduction

Inputs reviewed: Stage 1 Competency Questions; Stage 2 metadata dictionary and CQ coverage; Stage 3 SKOS taxonomy; Stage 4 ontology and CQ traceability; Stage 5 documentation, builder, queries, and private Development graph. No Held-out records, evaluation labels, predictions, or private evaluation claim specifications were inspected.

From the repository root:

```powershell
# One-time setup into an ignored, separate local package directory:
python -m pip install --target learning-local/stage6-deps -r knowledge-engineering/06-validation/requirements-local.txt
python knowledge-engineering/06-validation/validate_graph.py
```

Python 3.13, pySHACL 0.30.1 and RDFLib 7.2.1 were used. All local dependency versions are pinned in [requirements-local.txt](requirements-local.txt); production dependencies are unchanged. The validator reads the existing graph, loads the existing ontology and taxonomy separately, validates the shapes with Meta-SHACL, and runs SHACL Core with `inference='none'`, no imports, no advanced features and no network calls. It imports the guarded Stage 5 text-transform helper without executing the builder. No SHACL-SPARQL is needed.

Private results are written only to the existing ignored directory `knowledge-engineering/00-baseline/local-corpus/development/stage6/`: `shacl-report.ttl` and `results.json`. The latter records the graph/shapes hashes, focus counts, violations, integrity results, and all controls. Console output and this report contain aggregates only. No negative-control graph is written over the real graph; controls are fresh in-memory copies.

## Shapes and real-graph conformance

[shapes.ttl](shapes.ttl) defines **6 named, targeted node shapes**, containing **25 nested property shapes**. “Six shapes” refers to these six validation subjects, not the total number of SHACL shape resources. All six are exercised by real instances, with 30 total focus nodes. **Conforms: true; violations: 0; violation categories: none; shapes without matching instances: none.**

| Targeted node shape | Focus nodes | Enforced contract |
| --- | ---: | --- |
| EvidencePassage | 10 | Exactly one IRI referencing an EvidenceArtifact; exactly one locator string naming a non-root pointer and known transform; typed context references; optional text has the proper datatype. Full locator grammar and resolution are checked separately. |
| EvidenceArtifact | 3 | Exactly one nonempty location, 64-hex SHA-256 and valid UTC capture dateTime; an HTTP(S) original-source IRI. These are format/presence checks. |
| Responsibility | 3 | At least one IRI referencing an EvidencePassage. |
| SalaryObservation | 4 | At least one EvidencePassage; supplied bounds must be nonnegative xsd:decimal values, single-valued and ordered when both are present. Endpoints and currency/period/market/basis are not mandatory. |
| MachineAssessment | 7 | Target IRI with a type, kind, outcome, rationale, criteria, version, software attribution, activity reference, UTC generation time, and linked EvidencePassage. |
| JobPosting | 3 | At least one IRI referencing a JobRole; multiple roles remain allowed. |

These are deliberately scoped completeness rules for completed Stage 5 records, not changes to OWL semantics or universal rules for every future record. In particular, the required machine outcome does not prohibit the ontology's separate representation of unreviewed assessments in other workflows. Missing salary context stays unknown and never creates a negative assessment. No SalaryComparison shape was added: there are no pairs, and no comparison constraint is claimed as tested.

## Separate local source-integrity result

**Passed, with zero errors:**

- 3 of 3 referenced local artifacts exist.
- 3 of 3 SHA-256 checksums match both the graph and the fixed private Stage 5 mapping.
- 10 of 10 passage locators resolve against those verified artifacts.
- 10 of 10 stored passage texts match the resolved source text exactly.

These checks are Python file/locator checks, **not SHACL conformance**. Source paths must resolve to the three allowlisted Development case-specific files before they can be opened. Source/job identities, source URLs and capture timestamps also agree with the preserved case wrappers. No shared raw API response is opened. The validator checks JSON-pointer syntax and navigation, recognized transforms, integer offsets and strict span bounds; it does not silently truncate out-of-range spans. It uses the same documented HTML/text transform as Stage 5.

Matching hashes establish consistency with the retained local bytes and mapping, not independent authenticity. These artifacts are Stage 0 case-specific extracted original records, not the raw HTTP responses. The script does not establish that upstream publishers were truthful, captures were complete/authentic, extraction from shared raw responses was correct, or a cited passage semantically supports an assessment. A precisely located passage can still be irrelevant or misinterpreted.

## Executed controls

Six structural negative controls were rejected for their intended property and constraint component:

| In-memory modification | Conforms | Violations | Detected reason |
| --- | --- | ---: | --- |
| Remove one passage's artifact reference | False | 1 | MinCount on `inArtifact`. |
| Replace one artifact checksum with malformed text | False | 1 | Pattern on `sha256`. |
| Remove one artifact's original source | False | 1 | MinCount on `dcterms:source`. |
| Remove one assessment's evidence link | False | 1 | MinCount on `evidencePassage`. |
| Remove one assessment's generating activity | False | 1 | MinCount on `prov:wasGeneratedBy`. |
| Replace a salary bound with a nonnumeric string | False | 3 | Datatype, minimum-value and bound-comparison violations; the intended datatype violation is explicitly asserted. |

The six controls produce eight validation results in total, including the three consequences of one invalid salary value. These are test results, not violations in the real graph. Assertions inspect the intended result path/component rather than accepting any unrelated failure.

A positive control removed currency, period, market and basis properties from all four salary observations: **conforms true, zero violations**. The real graph's already-missing context also passes. No zero salaries, eligibility outcomes or other replacement values were added.

Three additional integrity controls demonstrate the separation of guarantees:

| In-memory modification | SHACL | Separate integrity check |
| --- | --- | --- |
| Replace one digest with a well-formed but wrong 64-hex value | Pass | Fails checksum matching; the three dependent passages are marked artifact-unverified. |
| Replace one locator with a well-formed pointer to a nonexistent field | Pass | Fails locator resolution. |
| Replace stored passage text with explicitly synthetic text | Pass | Fails exact source-text matching. |

All three were rejected by the intended integrity category. No original file was edited. Before/after hashes confirm the real graph and the three source artifacts remained unchanged throughout validation and controls.

## Stage 5 execution-identity correction

The former activity IRI depended only on builder/mapping hashes, so separate executions with different generation timestamps were presented as one PROV activity. The smallest correction was applied in [build_graph.py](../05-knowledge-graph/build_graph.py): import `uuid4` and use a fresh UUID for the activity IRI. The existing builder/mapping SHA-256 identifiers remain attached to the activity for reproducibility. Domain entity IRIs, evidence, source mapping, schema files, and domain assertions are unchanged.

Two actual rebuilds passed Stage 5 verification, including RDF parse/round-trip, vocabulary/property checks, artifact checksums, locators, numeric fidelity and all five SPARQL queries. They generated distinct activity IRIs. An exact comparison, excluding assessment and activity provenance records, confirmed unchanged domain triples relative to the pre-fix graph. Counts remain **3 cases, 37 entities, 231 ABox triples, 14 evidence links**, with SPARQL rows **3 / 0 / 4 / 7 / 0**. Assessment criteria hashes/times and activity identities change as expected. Assessments retain their current-result identifiers; this remains a snapshot, not an accumulating history.

The pre-fix snapshot, two corrected execution snapshots and `identity-check.json` are retained privately under `development/stage6/`. The corrected second execution is the graph validated here. [GRAPH.md](../05-knowledge-graph/GRAPH.md) now documents the correction. UUIDs and timestamps intentionally prevent byte-identical outputs across executions; content hashes and unchanged domain assertions supply reproducibility.

## Guarantees, CQ limits and boundary

Established for this graph: required typed links and provenance fields satisfy the six scoped shapes; numeric values satisfy the selected structural constraints; local evidence chains resolve to matching retained bytes/text; and known broken structures and integrity mismatches are detected. No semantic inference or automatic repair is performed. SHACL checks only targeted instances and the listed constraints; this is not exhaustive ontology validation or a guarantee against omitted facts/classes. Evidence relevance, accurate extraction interpretation, publisher identity, correct role assignments, salary eligibility, duplicate identity, and truth remain outside these guarantees.

- **CQ-01:** responsibility/evidence structure is checked; substantive relevance is still unanswered.
- **CQ-02:** posting-to-role links are checked; occupational assignment and core-versus-adjacent scope remain unanswered.
- **CQ-03:** salary evidence and provided bounds are checked; eligibility and complete compensation context remain unanswered.
- **CQ-04:** comparison pairs and comparability remain absent and unanswered.
- **CQ-05:** structural traceability and local resolution are demonstrated; approved claim support/contradiction and semantic correctness remain unanswered.
- **CQ-06:** machine assessment provenance is checked; review need, actual queue membership and completed human review remain unanswered.

Stage 6 is ready for technical review/approval within this limited scope. No production logic, dashboard, Actions, Stage 0 snapshot/corpus/split, ontology, taxonomy, or private evaluation label changed. No live collection, Ground Truth, accuracy/evaluation metrics, role assignments, comparison pairs, commit or push occurred. Work stops at Stage 6.

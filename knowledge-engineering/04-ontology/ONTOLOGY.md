# Stage 4 — Lightweight ontology design

21 October 2026 · Version 0.1 · Proposal for Haya and Lubna; team approval pending.

## Basis and method

The six [Stage 1 CQs](../01-scope/COMPETENCY_QUESTIONS.md) are the modeling contract. Inputs read: [Scope](../01-scope/SCOPE.md); Stage 2 [Vocabulary](../02-vocabulary-metadata/VOCABULARY.md), [Metadata Dictionary](../02-vocabulary-metadata/METADATA_DICTIONARY.md), [CQ Coverage](../02-vocabulary-metadata/CQ_COVERAGE.md); Stage 3 [Taxonomy](../03-taxonomy/TAXONOMY.md), [SKOS Turtle](../03-taxonomy/role-taxonomy.ttl), [Term Mapping](../03-taxonomy/TERM_MAPPING.md); Stage 0 [Audit](../00-baseline/AS_IS_AUDIT.md), [Evaluation Protocol](../00-baseline/EVALUATION_PROTOCOL.md), and [Closeout](../00-baseline/STAGE_0_CLOSEOUT.md). All required inputs exist and are readable. Git was clean at `bdad074` on `main` before work. Earlier documents retain approval-pending language; the continuation instruction authorizes using them as the working design basis, without recording team approval of their semantics or evaluation decisions.

Method follows the local [Ontology Pipeline](../../learning-local/Ontology-Pipeline.md), “Competency questions: The ontology’s contract” and “Ontology design heuristics” (lines 5127–5310), then its schema-first sequence (5311–5358): trace every term to a CQ, reuse standards, distinguish roles from agents and SKOS from OWL, use safe inferential domains/ranges, and document uncertainty. Earlier documents’ sibling learning-text link is unavailable here; the readable `learning-local/` copy supplies the method. Suggested ABox and reasoner exercises are deferred because this stage explicitly prohibits instance data.

`ke:` = `urn:ke-market-observatory:ontology:`; ontology IRI = `urn:ke-market-observatory:ontology`. Proposed stable local URNs assert no hosted resolution service. Preserve identifiers across label edits; meaning/namespace changes require a versioned decision. [ontology.ttl](ontology.ttl) contains schema only. [CQ_TRACEABILITY.md](CQ_TRACEABILITY.md) describes future answer paths and limits, without implemented queries or evaluations.

## Classes

Only independent targets and provenance boundaries get classes. Compensation basis, career level and pay market remain literal context; source actors reuse `prov:Agent`. Review need is an Assessment question; Human Review is a HumanAssessment. No class is created per outcome, missing field or taxonomy concept. CQ numbers abbreviate CQ-01 through CQ-06.

| Class | Meaning / exclusion | Superclass | CQs |
| --- | --- | --- | --- |
| JobPosting | A source-published advertisement of offered work; not a unique hiring request or every legacy source record. | — | 01,02,03,04,05,06 |
| Requisition | An employer hiring request; link only with documented identity evidence. | — | 04,06 |
| JobRole | A work function advertised through duties; not a title string, person or occupational SKOS concept. | — | 01,02,04 |
| Responsibility | An activity expected of the advertised role; excludes qualifications, company descriptions and incidental terms. | — | 01,02,05 |
| KnowledgeRepresentation | Explicit concepts, entities, relationships or meaning represented in the work; actual deployed artifact identity can remain unknown. | — | 01,02 |
| SalaryObservation | An attributable compensation amount/range statement and context; not evidence, verified base pay or an eligibility judgment. | prov:Entity | 03,04,05 |
| EvidenceArtifact | A preserved original source capture with original identity, capture time and byte checksum; not merely a live URL. | prov:Entity | 01,02,03,04,05,06 |
| EvidencePassage | A precisely located part of one capture with necessary context; linkage alone does not establish support. | prov:Entity | 01,02,03,04,05,06 |
| Claim | A bounded attributable factual assertion with a stable version; its text may remain unresolved and membership does not assert truth. | prov:Entity | 05,06 |
| Assessment | A recorded determination about one scoped question, with target, origin, criteria, reasons and uncertainty; a result entity, not the evaluation activity. | prov:Entity | 01,02,03,04,05,06 |
| MachineAssessment | An assessment produced by identified software; never automatically a human judgment or Ground Truth. | ke:Assessment | 01,02,03,04,05,06 |
| HumanAssessment | A documented human determination, including review/adjudication; preserves independent initial judgments. | ke:Assessment | 01,02,03,04,05,06 |
| SalaryComparison | A record of two explicitly designated observations and declared endpoint/conversion policies; no automatic pairing or comparability follows. | prov:Entity | 04 |
| ReviewQueueEntry | An observed application queue item in a specific snapshot; distinct from a flag, assessed need or completed review. | prov:Entity | 06 |

## Properties

Unprefixed names use `ke:`. A dash means no global domain/range axiom, deliberately avoiding unintended typing of heterogeneous targets. Each nonempty domain/range below is encoded once. Domains/ranges infer types; they do not validate completeness. No functional properties, keys, cardinalities, disjointness, equivalence, property chains, transitivity, inverses or identity rules are asserted.

Evidence requirements describe a future provenance contract, not OWL existence restrictions or implemented validation. Unsupported interpretations stay candidate claims/assessments, rather than asserted duty, role, band or identity facts.

### Object properties

| Property | Domain | Range | Meaning | CQs | Evidence / provenance requirement |
| --- | --- | --- | --- | --- | --- |
| advertisesRole | JobPosting | ke:JobRole | Relates an advertisement to a described work function. | 01,02,04 | Original duties and interpretation; several functions may coexist. |
| hasResponsibility | JobRole | ke:Responsibility | Relates a work function to an advertised duty. | 01,02,05 | Duty passage and context; no title/skill-hit derivation. |
| actsOnRepresentation | Responsibility | ke:KnowledgeRepresentation | Relates a duty to explicit knowledge/meaning it acts on or substantively uses. | 01,02 | Action/object passage and rationale; omit unresolved links. |
| roleConcept | JobRole | skos:Concept | Describes a function with an existing occupational concept. | 01,02,04 | Evidence-backed interpretation against Stage 3 definitions, with assessment provenance; no lexical auto-assignment. |
| advertisesRequisition | JobPosting | ke:Requisition | Relates a posting to a substantiated employer hiring request. | 04,06 | Documented identity decision and source identifiers; never similarity/URL inference. |
| possibleSameRequisitionAs | JobPosting | ke:JobPosting | Records suspected identity overlap for review, without equality. | 04,06 | Attributed identity-review assessment and evidence; not transitive or owl:sameAs. |
| hasSalaryObservation | JobPosting | ke:SalaryObservation | Relates a posting to a separately preserved compensation statement/band. | 03,04,05 | Original structured/prose passage; retain each band separately. |
| salaryForRole | SalaryObservation | ke:JobRole | Relates a band to the advertised function it explicitly applies to. | 03,04 | Band-to-role applicability evidence; no blanket applicability. |
| evidencePassage | — | ke:EvidencePassage | Links a record to relevant candidate/contextual evidence, without asserting support. | 01,02,03,04,05,06 | Resolvable passage chain; an Assessment explains support, contradiction or uncertainty. |
| inArtifact | EvidencePassage | ke:EvidenceArtifact | Locates a passage in its preserved capture. | 01,02,03,04,05,06 | Exact artifact reference, checksum, capture time and locator. |
| contextPassage | EvidencePassage | ke:EvidencePassage | Points to another passage needed to interpret the first, including conflicting wording. | 01,02,03,04,05,06 | Context with its own locator; no consistency assumption. |
| claimSubject | Claim | — | Identifies the subject of a bounded assertion. | 05,06 | Fixed claim definition/version; omit unresolved subjects. |
| assessmentTarget | Assessment | — | Identifies the record, role, claim, observation, comparison or assessment being judged. | 01,02,03,04,05,06 | Explicit target and question kind; no target-type inference or verdict. |
| comparisonMember | SalaryComparison | ke:SalaryObservation | Identifies an observation in an already designated pair. | 04 | Fixed pair reference; intended two distinct members, documented rather than OWL-enforced. |
| reviewsAssessment | HumanAssessment | ke:Assessment | Links later review/adjudication to an earlier determination. | 01,02,03,04,05,06 | Reviewer, time, criteria, version and rationale; preserve initial judgments. |
| queueTarget | ReviewQueueEntry | — | Identifies the actual record routed to this observed queue item. | 06 | Application snapshot, original record identity and category; never fabricate membership from a flag. |

### Datatype properties

Literal context avoids separate currency, period, geography and level ontologies. Strings preserve evidenced meanings without closed enumerations. Unsupported units or malformed amounts can remain in evidence without inventing a usable decimal observation.

| Property | Domain | Range | Meaning | CQs | Evidence / provenance requirement |
| --- | --- | --- | --- | --- | --- |
| actionText | Responsibility | xsd:string | Advertised action wording. | 01,02 | Duty passage; do not connect unrelated words. |
| lowerAmount | SalaryObservation | xsd:decimal | Original numeric amount or lower bound. | 03,04 | Exact units/band; preserve malformed raw input in evidence instead of inventing valid amounts. |
| upperAmount | SalaryObservation | xsd:decimal | Original ceiling when disclosed. | 03,04 | Explicit ceiling; no invented range. |
| currency | SalaryObservation | xsd:string | Explicit currency for this amount. | 03,04 | Band-specific evidence; never transfer units from unrelated benefits/bands. |
| payPeriod | SalaryObservation | xsd:string | Explicit pay period, preserving original meaning. | 03,04 | Band-specific evidence; never infer Annual or Monthly. |
| compensationBasis | SalaryObservation | xsd:string | Source-described base, total compensation, OTE, bonus, equity or other measure. | 03,04 | Explicit wording; separate from evidence status and eligibility. |
| grossNetBasis | SalaryObservation | xsd:string | Explicit gross/net measure when stated. | 03,04 | Source passage; no tax or gross/net conversion assumed. |
| payMarket | SalaryObservation | xsd:string | Evidenced country and geographic pay-market scope. | 03,04 | Band geography; headquarters/city/remote eligibility alone are insufficient. |
| bandApplicability | SalaryObservation | xsd:string | Conditions determining who/where a particular band applies to. | 03,04 | Original conditions; no pooling or favorable-band selection. |
| careerLevel | JobRole | xsd:string | Explicitly evidenced career level of the advertised work. | 02,04 | Contextual evidence; title-derived machine levels remain assessments, not this fact. |
| employerName | SalaryObservation | xsd:string | Name explicitly attributed to the hiring employer. | 03,04,05 | Employer/client evidence; recruiter/ATS labels cannot fill missing identity. |
| recruitingAgentName | SalaryObservation | xsd:string | Name explicitly attributed to the recruiting agent. | 03,04,05 | Agency attribution; separate from publisher and employer. |
| artifactLocation | EvidenceArtifact | xsd:anyURI | Resolvable preserved-capture location, distinct from original source URL. | 01,02,03,04,05,06 | Capture manifest; private paths remain private, never automatically published. |
| sha256 | EvidenceArtifact | xsd:string | SHA-256 of exact captured artifact bytes. | 01,02,03,04,05,06 | Capture-generated byte checksum; no implication of truth. |
| capturedAt | EvidenceArtifact | xsd:dateTime | UTC original-source capture time. | 01,02,03,04,05,06 | Actual capture record; not publication, assessment or verification time. |
| passageLocator | EvidencePassage | xsd:string | Exact pointer, page/section or bounded span with transform/offset convention. | 01,02,03,04,05,06 | Must resolve against hashed capture; URLs/summaries alone are insufficient. |
| passageText | EvidencePassage | xsd:string | Optional verbatim text retained alongside its locator. | 01,02,03,04,05,06 | Must match capture under the stated transform; text alone is not a trace chain. |
| claimText | Claim | xsd:string | Bounded assertion selected for support assessment. | 05 | Approved/attributable definition and version; unresolved text is omitted, never synthesized. |
| assessmentKind | Assessment | xsd:string | Scoped question, separate from outcome and origin. | 01,02,03,04,05,06 | Use question/target conventions below; retain legacy codes separately. |
| outcome | Assessment | xsd:string | Recorded result under stated criteria, including Insufficient Evidence. | 01,02,03,04,05,06 | Origin, evidence and rationale; absent outcome is unreviewed, never false. |
| rationale | Assessment | xsd:string | Explanation of determination and material evidence/conflicts. | 01,02,03,04,05,06 | Specific duty, band, claim or identity evidence; no invented facts. |
| unresolvedFact | Assessment | xsd:string | Specific missing/conflicting fact affecting the decision. | 01,02,03,04,05,06 | Name field and impact; unrelated gaps need not force uncertainty. |
| dimensionReason | Assessment | xsd:string | Dimension-named outcome and reason in a scoped assessment. | 01,02,03,04,05,06 | Identify dimension, comparison member and passages; do not hide unknowns behind an aggregate verdict. |
| criteriaReference | — | xsd:string | Versioned criteria, pair specification or frozen-assumption reference. | 01,02,03,04,05,06 | Stable document/version/checksum on Assessment or SalaryComparison; no domain that conflates their types. |
| endpointPolicy | SalaryComparison | xsd:string | Declared floor or full-range endpoint policy. | 04 | Fixed before judging; full ranges require both ceilings. |
| conversionPolicy | SalaryComparison | xsd:string | Reference to frozen FX rates/date, period conversion and rounding. | 04 | Immutable reference; preserve original units/amounts; conversion does not prove comparability. |
| queueCategory | ReviewQueueEntry | xsd:string | Original category of observed queue item. | 06 | Actual snapshot field; not a human outcome. |
| internalReviewFlag | — | xsd:boolean | Recorded internal machine review flag on a source record/output snapshot. | 06 | Run/snapshot attribution; absence is unknown; neither value proves membership or human need. |
| reviewQuestion | Assessment | xsd:string | Specific issue a reviewer must resolve for an assessed review need. | 06 | Affected decision, material missing/conflicting fact and evidence; no automatic queue action. |

### Reused vocabulary

External terms are referenced without redeclaration, copied schemas, automatic downloads or `owl:imports`.

| Term | Meaning / domain-range considerations | CQs | Evidence / provenance requirement |
| --- | --- | --- | --- |
| skos:Concept, skos:ConceptScheme and existing labels | Occupational concepts and unchanged scheme, not OWL classes. `roleConcept` ranges over Concept. | 01,02,04 | Stage 3 definitions/identifiers; no title-derived verdicts. |
| prov:Entity | Provenance-bearing records; declared superclass of observations, captures, passages, claims, assessments, comparisons and queue snapshots. | 01–06 | No truth, verification or public-availability implication. |
| prov:Agent, prov:Person, prov:SoftwareAgent | Existing types for identifiable responsible people/software and publishers. | 01–06 | Identify only when known; JobRole is a work function, not an agent. |
| prov:wasAttributedTo | Entity → Agent: responsibility for a record/claim/assessment, not endorsement or support. | 01–06 | Assessment author/reviewer or software producer; preserve source assertion attribution separately. |
| prov:wasGeneratedBy, prov:Activity | Entity → Activity: generating run or documented review event. | 01–06 | Stable run/event ID/version; a run is an activity, not a SoftwareAgent. |
| prov:generatedAtTime | Entity → xsd:dateTime: assessment generation or queue-snapshot time. | 01–06 | Actual UTC time; separate from source capture/publication. |
| dcterms:identifier | Identifier, used here as a literal for scoped posting, channel, record and run IDs; no local domain restriction. | 01–06 | Preserve authority/scope with source context; not a key or requisition proof. |
| dcterms:title, dcterms:description | Literal original titles, duty wording, represented knowledge and stated experience/context; no local domain restriction. | 01,02,04,05 | Original text and evidence; summaries cannot replace passages. |
| dcterms:source | Resource from which a described resource is derived: original URL of capture or frozen pair-specification reference. | 03,04,05,06 | Actual resource reference; not support, archived content or unique identity. |
| dcterms:publisher | Resource → Agent: entity responsible for making source material available. | 03,05,06 | Distinguish publisher, ATS/channel, recruiting agent and employer; retain channel identifier separately. |
| owl:versionInfo | Annotation for ontology, claim and assessment versions; literal version convention. | 01–06 | Preserve previous versions and provenance; not approval or Ground Truth status. |

Published meanings: [RDFS](https://www.w3.org/TR/rdf-schema/), [SKOS](https://www.w3.org/TR/skos-reference/), [PROV-O](https://www.w3.org/TR/prov-o/), [DCMI Terms](https://www.dublincore.org/specifications/dublin-core/dcmi-terms/). No new software dependency is required for the model.

## Assessment contract and uncertainty

Separate Assessment records by target, question, origin and version. MachineAssessment and HumanAssessment are explicit origin specializations with no automatic translation. Undocumented curated judgments remain generic assessments with known attribution, never presumed independent human labels. Do not type one determination as both human and machine: human review creates a new record through `reviewsAssessment`. Independent reviews and adjudication retain separate identities, reviewer/time, criteria, version and rationale. HumanAssessment membership does not establish reviewer independence, finality or Ground Truth.

Kind strings identify questions, not classification rules. Human outcomes below reuse Protocol §1. Machine outputs keep original codes with criteria/run provenance and are not silently mapped to human labels.

| assessmentKind | Intended target | Human outcome convention | Explanation required |
| --- | --- | --- | --- |
| relevance | JobPosting, with duty/role evidence | Relevant / Not relevant / Insufficient Evidence | Substantive versus incidental action/object use; completeness of negative evidence. |
| role scope | JobRole | Core KE / Adjacent technical / Neither / Insufficient Evidence | Duties establishing primary versus substantive supporting work. |
| salary eligibility | SalaryObservation; JobPosting if no pay observation exists | Eligible / Ineligible / Insufficient Evidence | Basis, units, attribution, band, missing/conflicting facts; independent of relevance. |
| comparability | SalaryComparison; explicitly unpaired posting for Not applicable | Comparable / Not comparable / Insufficient Evidence / Not applicable | Per-member eligibility and dimension reasons; no empty comparison for an unpaired posting. |
| evidence support | Claim | Supported / Unsupported / Insufficient Evidence | Passage-specific support, contradiction or failure to substantiate; distinguish incomplete capture. |
| review need | Affected record or scoped Assessment | Yes / No / Insufficient Evidence | Decision affected, material unresolved facts, scoped reasons and reviewQuestion. |
| identity review | Suspected posting overlap | No new outcome vocabulary fixed here | Human decision or unresolved issue; no new duplicate adjudication rule. |

Missing properties/assessments mean unknown or unrecorded. An assessment without an outcome is unreviewed; explicit Insufficient Evidence records a judgment of uncertainty. Negatives require evidence/criteria. No absent-field defaults, closed-world negation, synthetic Unknown individuals or fake zero salaries are introduced. `unresolvedFact` identifies material missing information; unrelated gaps need not overturn a definite negative.

CQ-04 uses one SalaryComparison per already designated pair, with two distinct `comparisonMember` values and a frozen specification in `dcterms:source`/`criteriaReference`. Pair size is documented, not an OWL cardinality. Each observation retains its separate eligibility assessment. Comparison `dimensionReason` entries identify member, dimension, finding, passages and gaps: country/pay market, role scope/duties, explicitly evidenced career level and experience context, gross base-pay measure, attribution/band applicability, endpoints and conversion. Similarity requires a judgment about work; concept equality alone is insufficient. No pair is assigned now.

## Semantic boundaries and evidence

- **Posting / requisition:** similar titles, URLs, IDs or grouping tags cannot establish hiring-request identity. `possibleSameRequisitionAs` preserves suspicion; `advertisesRequisition` needs a documented identity decision. No `owl:sameAs` is introduced.
- **Role / duty:** a function can have several duties. A Responsibility retains action/object evidence; a KnowledgeRepresentation can describe a mention without claiming a uniquely identified deployed artifact. Qualifications or keywords alone create neither duty facts nor relevance judgments.
- **Observation / evidence:** preserve each amount/band and its original structured/prose passages separately. Disagreeing observations or interpretations need separate provenance rather than unqualified conflicting scalar values on one record. A complete no-pay posting can have an eligibility assessment without a fabricated observation; an incomplete source remains unresolved.
- **Pay meaning / use:** base, total, OTE, bonus and equity retain distinct wording. `estimate`/`unverified` are evidence status, not bases. Never infer period, currency, employer, experience/level, gross pay or unique requisition. Do not invent ceilings, merge bands or choose favorable bands. The USD/GBP/EUR/SAR and Annual/Monthly eligibility policy is unchanged; documenting other source units does not make them eligible. Normalization, eligibility, comparability and global benchmark admission remain separate; no admission rule/property is added.
- **Claim / passage / judgment:** `Claim → evidencePassage → inArtifact` yields candidate evidence, not support. Each passage has its locator and necessary `contextPassage`; each artifact has original source URL/identifiers, publisher, preserved location, checksum and capture time. Claim text, version and attribution stay separate. An evidence-support Assessment targets the claim and cites the exact passages, with rationale explaining support, contradiction or uncertainty. Assessments may disagree. Neither attribution, claim membership nor a complete chain makes the assertion true; unresolved claim definitions remain unresolved.
- **Need / flag / queue / completed review:** assessed review need, `internalReviewFlag`, timestamped ReviewQueueEntry and documented HumanAssessment are separate records/facts. Queue absence/disappearance proves neither No review need nor resolution. Override ID lists do not become completed independent reviews. Preserve snapshot time, source record ID and category, retaining the existing `(id, category)` distinction; missing snapshots stay unknown.

## Stage 3 integration

Reference/load the existing `role-taxonomy.ttl` separately and unchanged. Its namespace stays `urn:ke-market-observatory:role:`; scheme `role:scheme`; concepts `role:knowledge-engineer`, `role:ontology-engineer`, `role:knowledge-graph-engineer`, `role:semantic-web-engineer`. Ontologist remains the existing scoped alternative label. Future JobRoles may reference these IRIs with `roleConcept` after evidence-backed interpretation. Several concepts or none may apply; unmapped does not mean irrelevant. This schema repeats no taxonomy declarations and creates no assignments.

No SKOS concept becomes an OWL class; no `rdf:type role:...` classification is prescribed. `skos:broader` is never mapped to `rdfs:subClassOf` and does not propagate posting duties, eligibility or comparability. `roleConcept` ranges over SKOS concepts without a scheme-specific axiom; use of this particular scheme is a documented integration convention, not an implemented validator.

## Exclusions and team decisions

No production code/data/classifier/routing, frozen baseline/corpus/splits or private material changes. No held-out evidence, labels, predictions or private claim specifications were read. Public design documents sufficed; no case examples, instances, graph population, executable mappings, SPARQL, SHACL, inference rules, reasoner test individuals or evaluations are included. Schema coverage makes no accuracy/CQ-answer success claim.

Haya and Lubna should decide:

1. Approve class/property scope, local URNs/version policy and SKOS convention; retain earlier term/hierarchy approval issues.
2. Confirm literal pay-market, basis, attribution and career-level context is sufficient for this pilot; structured value vocabularies need demonstrated CQ value before extension.
3. Approve assessment-kind strings, provenance/version requirements, dimension reasons and explicit uncertainty. Later validation may enforce provenance completeness and pair size; these are not OWL restrictions here.
4. Agree the precise locator/transform contract, identifier authorities and private/public boundaries before population. Missing provenance stays missing; private captures are not published by this design.
5. Retain claim approvals, duplicate identity, independent labeling/adjudication and final evaluation for their authorized phase. Any new comparability output/scoring interface needs the protocol’s separate versioned approval.

## Validation record

Validation on 21 October 2026 used the installed Python 3.13 standard library. RDFLib, PyOxigraph, Node N3/RDFLib and command-line RDF parsers were unavailable in the checked installations; no dependency was installed. The complete file was parsed against its deliberately restricted Turtle grammar: prefix declarations, one named-subject triple per line, named predicates (or `a`), named objects or short string literals with optional language tags. This subset excludes blank nodes, collections, shorthand lists, multiline strings and typed instance literals; none occur in the schema. The checker rejects any unconsumed/unsupported line, validates string escapes and resolves every prefix.

Results: **passed — 274 unique schema triples; 14 classes, 16 object properties, 29 datatype properties and one ontology declaration**. Additional structural checks confirmed declared local references, a label/definition/CQ reference per term, provenance comments per property, at most one domain/range per property, appropriate object/datatype ranges and exact agreement with the documentation tables. No domain instances, taxonomy declarations, imports or identity/rule axioms occur. All three Stage 3 files retain their pre-work SHA-256 checksums. Final Git inspection found only the three new Stage 4 files; existing tracked artifacts remained unchanged.

This is a complete syntax check for the subset actually used, not a general Turtle-parser conformance test, OWL consistency proof, SHACL validation or successful CQ execution. Broader RDF parsing, inference behavior and data completeness remain untested. No instance data were constructed for validation.

The syntax-only check is reproducible from the repository root using this Python code (no external packages):

```python
from pathlib import Path
import re

iri = r'<[^<>"{}|^`\\\x00-\x20]+>'
qname = r'[A-Za-z][A-Za-z0-9_-]*:[A-Za-z][A-Za-z0-9_-]*'
node = rf'(?:{iri}|{qname})'
literal = (r'"(?:[^"\\\r\n]|\\(?:[tbnrf"\x27\\]|'
           r'u[0-9A-Fa-f]{4}|U[0-9A-Fa-f]{8}))*"'
           r'(?:@[A-Za-z]+(?:-[A-Za-z0-9]+)*)?')
prefix = re.compile(rf'@prefix\s+([A-Za-z][A-Za-z0-9_-]*):\s+({iri})\s*\.')
triple = re.compile(rf'({node})\s+(a|{node})\s+({node}|{literal})\s*\.')
namespaces, count = {}, 0
for number, line in enumerate(Path(
    'knowledge-engineering/04-ontology/ontology.ttl'
).read_text(encoding='utf-8').splitlines(), 1):
    line = line.strip()
    if not line or line.startswith('#'):
        continue
    match = prefix.fullmatch(line)
    if match:
        assert match[1] not in namespaces, (number, 'duplicate prefix')
        namespaces[match[1]] = match[2][1:-1]
        continue
    match = triple.fullmatch(line)
    assert match, (number, 'outside supported Turtle subset')
    for term in match.groups():
        if term != 'a' and not term.startswith(('<', '"')):
            assert term.split(':', 1)[0] in namespaces, (number, term)
    count += 1
print('Turtle subset syntax passed:', count, 'triples')
```

Stop after Stage 4. No commit or push was made.

# Stage 0 — Step 0.3B: Fixed corpus inventory

Corpus ID: `20261021T125408Z-ebb0b062`. This is a prospective source capture, not historical reconstruction or Ground Truth. Full machine-readable metadata, case/group IDs, source IDs, raw/per-case artifact hashes and split allocation are in [corpus-inventory.json](corpus-inventory.json). Source-only review data and all original records remain local under the ignored directory.

## Capture and availability

Captured 2026-10-21T12:54:08.183Z through 2026-10-21T12:54:33.287Z UTC: **300 raw posting occurrences, 263 distinct (source ID, upstream posting ID) identities**, across six configured sources. There were 83 read-only GET requests, including 77 Greenhouse detail responses acquired without relevance filtering. All board feeds completed; no source was added and no FX endpoint was contacted. The initial sandbox-blocked attempt captured no postings and is retained separately under the same ignored root.

| Configured source | Raw occurrences | Distinct upstream IDs | Selected |
| --- | ---: | ---: | ---: |
| lever-sambatv | 61 | 61 | 10 |
| greenhouse-nearform | 20 | 20 | 4 |
| greenhouse-tamara | 44 | 44 | 4 |
| greenhouse-sapience | 13 | 13 | 11 |
| workable-envision | 55 | 55 | 6 |
| workable-robusta | 107 | 70 | 5 |

Raw HTTP response bytes were written and hashed before parsing/classification. Per-record artifacts retain exact response pointers. Complete description, compensation, country/location and other fields are preserved **as supplied by the public APIs**. Upstream omissions cannot be ruled out. Original responses, parsed originals and derived replay inputs are distinguished; no description was reconstructed from normalized production records.

## Selection and split

The exact frozen classifier is from baseline HEAD `ee5bd15ff52b6a88e15a2dafab6886422980f557`; Git-blob SHA-256 `207ef7426790d2a56ac24b06207e77b8ae50bc8a19b117d98d407f74c8118908`. Only its existing pure functions were executed offline; the production refresh pipeline was not invoked.

| Population | Approved | Pending | Excluded |
| --- | ---: | ---: | ---: |
| Raw occurrences | 8 | 7 | 285 |
| Distinct source/job identities | 7 | 7 | 249 |
| Eligible conservative group representatives | 5 | 7 | 229 |
| Selected | 5 | 7 | 28 |
| Development | 1 | 2 | 7 |
| Held-out | 4 | 5 | 21 |

**40 selected postings: 10 development, 30 held-out.** These groups are sampling outcomes, not human labels. The proposed 15 approved / 10 pending / 15 excluded allocation was unavailable: approved/pending shortfalls of 10 and 3 after grouping were filled with excluded cases. No examples or labels were fabricated.

Grouping joins shared upstream IDs, canonical-like supplied URLs, same-board normalized titles, or identical long description inputs. There are 241 conservative groups, 38 containing multiple raw occurrences. This deliberately groups some potentially distinct same-title requisitions; it is an anti-leakage precaution, not resolution of employer/client identity. Each selected case has a distinct upstream identity and one representative per group; no known group crosses the split. Residual semantic duplicates remain possible.

Seed: `ke-observatory-step-0.3B-2026-10-21-v1`. Conservative ID/URL/same-board-title/identical-long-description groups; representative by SHA256(seed+caseID), artifact path tie-break. Take up to 15 approved and 10 pending representatives. Fill shortage from excluded with source coverage, three candidates per observed lexical pay/semantic-term feature, then least-used source and seeded order. Largest-remainder proportional split allocation, then independent seeded order within each machine stratum.

The local sampling ledger preserves every group member, grouping link, representative, sampling stratum and split. Per-case machine strata are omitted from shareable/reviewer-facing rows to reduce reviewer cueing.

## Salary evidence coverage

| Observable marker | All 300 occurrences | Selected 40 |
| --- | ---: | ---: |
| Structured band present | 45 | 9 |
| Literal base-pay wording present | 45 | 16 |
| Literal total-compensation/OTE wording present | 26 | 5 |
| Currency-before-number text pattern | 59 | 20 |
| Neither structured band nor that currency pattern | 219 | 15 |
| Frozen parser retains numeric pay | 22 | 4 |
| Frozen parser marks salary eligible | 0 | 0 |

Markers overlap and are **not human eligibility or ineligibility judgments**. Missing detector matches do not prove no disclosed salary. Free-text pay stays available in original descriptions even where dedicated pay fields are empty. The retained numeric bands have unknown basis under the frozen parser. Human review is needed to determine whether enough assessable positive/negative salary cases exist. No multi-band structured examples were observed; no publisher-estimate/repost cases or outside sources were added to fill that gap.

No comparison pairs are assigned in this source-only preparation. Approve fixed partners and scope/endpoint rules before labeling, or record the shortage if meaningful pairs cannot be established. Deterministic literal claim excerpts may be introductory or HTML-formatted; approve their suitability before labeling and version any correction.

## Local review and replay materials

- Local run: `knowledge-engineering/00-baseline/local-corpus/20261021T125408Z-ebb0b062/`.
- Local source-only CSV: `evaluation-cases.csv`, copied from the unchanged 28-column template. All human decisions, reasons, rationale, uncertainty status, reviewer/adjudication/date/version fields, and comparison partners are blank.
- `selected/<case_id>/evidence.json` holds original title, full description fields, salary/free-text context, as-supplied geography and artifact references. `replay-input.json` is the captured board record overlaid with captured detail using the existing adapter merge semantics.
- `raw/`, `originals/`, `details/`, `capture-manifest.json`, `candidate-inventory.json` and `sampling-ledger.json` preserve the complete capture and selection audit trail. Keep machine ledgers away from blinded reviewers.

Local artifact seal SHA-256 (`SHA256SUMS`): `95ccf792916728d6c49a3059a9c053b6021db6c1a48c8c41353bdb295be13e9c`. The seal covers original, selected and preparation metadata artifacts; checksums identify content, not source truth. Raw and review files must remain local; use a separately versioned copy for later authorized labeling.

## Verification and privacy

Verification passed for 83 original responses, all 300 candidate occurrences and all 40 selected cases. Every selected input matches captured originals, references resolve, source IDs are stable, required review fields are blank, and known duplicate groups do not cross splits. Every raw/local artifact is ignored and none is tracked. Raw JSON was saved before the frozen classifier ran.

The sole existing-file edit is the anchored ignore rule `/knowledge-engineering/00-baseline/local-corpus/`. All 44 other pre-existing tracked files remain byte-identical, including production code/data/workflow/dashboard, protocol/template, and the approved baseline snapshot/seal. No refresh, deployment, source expansion, human labeling, KE implementation, accuracy/improvement calculation, commit or push occurred.

This shareable inventory contains IDs, aggregate counts, selection details, hashes and local relative references, with no source descriptions, excerpts, titles, or contact information. Git ignore does not prevent force-adding files: do not force-add local evidence. Future public copies must follow the same metadata-only policy.

## Selected case index

| Case ID | Source ID | Split |
| --- | --- | --- |
| EVAL-017f9b803aff4ee2 | lever-sambatv | held_out |
| EVAL-0d7b2c3f9f39cbcc | greenhouse-sapience | development |
| EVAL-1dc856a41d2f7cc2 | lever-sambatv | held_out |
| EVAL-2ad65cdb9282c914 | greenhouse-tamara | held_out |
| EVAL-31af8a786043d9e1 | workable-envision | held_out |
| EVAL-36707052e3cea413 | workable-envision | held_out |
| EVAL-3dfa6491679e5c52 | lever-sambatv | held_out |
| EVAL-439ca061404674c2 | lever-sambatv | held_out |
| EVAL-4847917fd586d111 | lever-sambatv | development |
| EVAL-4944ef8ed5a21584 | lever-sambatv | held_out |
| EVAL-49b310c87a8d7de7 | workable-robusta | development |
| EVAL-4bc2915a9cd47faf | workable-robusta | held_out |
| EVAL-5808d42f328be89c | greenhouse-sapience | development |
| EVAL-582da882867d643d | lever-sambatv | held_out |
| EVAL-5af2e060050ee95a | lever-sambatv | held_out |
| EVAL-5cc434f061607dd4 | workable-robusta | held_out |
| EVAL-650a7e36f8e9ebc7 | lever-sambatv | development |
| EVAL-66c11680641b7955 | greenhouse-sapience | held_out |
| EVAL-727eedc183a19856 | greenhouse-sapience | held_out |
| EVAL-78b69dbc5f1ce9b9 | greenhouse-nearform | held_out |
| EVAL-859b464d7ec70521 | greenhouse-nearform | development |
| EVAL-88e5a3055132360d | greenhouse-tamara | held_out |
| EVAL-8ae988f379d45485 | greenhouse-tamara | held_out |
| EVAL-934ded31907cd29b | workable-envision | held_out |
| EVAL-953f881586ca4f3d | greenhouse-sapience | held_out |
| EVAL-95e13d712cf8c19f | workable-envision | held_out |
| EVAL-96dbed73c1886ec2 | greenhouse-sapience | held_out |
| EVAL-a263ee5d31a85961 | lever-sambatv | held_out |
| EVAL-bcc759c2ff1a0e4d | greenhouse-sapience | held_out |
| EVAL-d1d0a61c7b1ca072 | greenhouse-tamara | development |
| EVAL-d3e7c52d1ad61855 | workable-envision | development |
| EVAL-d4068f29eae794a2 | greenhouse-nearform | held_out |
| EVAL-d59713c2dce0d763 | greenhouse-sapience | held_out |
| EVAL-dafb394f04fdd989 | greenhouse-sapience | held_out |
| EVAL-e0f88fce2d2e186c | greenhouse-sapience | held_out |
| EVAL-e4604c3b343c0f9c | greenhouse-nearform | held_out |
| EVAL-ee7d1d903fd4c40a | greenhouse-sapience | held_out |
| EVAL-f41e6441d739ab74 | workable-robusta | development |
| EVAL-f5abd1d8389ba873 | workable-robusta | development |
| EVAL-fa95bb10fd034323 | workable-envision | held_out |

Stop after corpus preparation. Review the distribution shortages, conservative grouping, source availability and claim/pair suitability before beginning human labeling.

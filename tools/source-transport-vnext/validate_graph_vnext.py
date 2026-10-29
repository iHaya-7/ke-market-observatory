"""Experimental SHACL plus byte/pointer/span and RDF assertion fidelity checks."""
import base64

import graph_vnext as builder
import consumer_vnext as consumer
import transport_vnext as transport
from rdflib import Graph
from rdflib.namespace import OWL, RDF
from rdflib.compare import isomorphic
from pyshacl import validate

KE, VX, PROV = builder.KE, builder.VX, builder.PROV


def one(graph, subject, predicate):
    values = list(graph.objects(subject, predicate))
    transport.require(len(values) == 1, 'Expected exactly one ' + str(predicate))
    return values[0]


def shacl(graph, shapes, schema):
    conforms, report, _ = validate(graph, shacl_graph=shapes, ont_graph=schema,
                                   inference='none', advanced=False, inplace=False,
                                   do_owl_imports=False, meta_shacl=True)
    sh = builder.Namespace('http://www.w3.org/ns/shacl#')
    rows = list(report.subjects(RDF.type, sh.ValidationResult))
    return bool(conforms), len(rows)


def validate_graph(graph, packet, consumed):
    builder.check_consumer(packet, consumed)
    schema = Graph().parse(transport.ROOT / 'knowledge-engineering/04-ontology/ontology.ttl')
    vocabulary = Graph().parse(builder.HERE / 'vocabulary_vnext.ttl')
    for subject, predicate, obj in graph:
        if str(predicate).startswith(str(KE)):
            transport.require((predicate, None, None) in schema, 'Undeclared frozen ontology property')
        if predicate == RDF.type and str(obj).startswith(str(KE)):
            transport.require((obj, RDF.type, OWL.Class) in schema, 'Undeclared frozen ontology class')
        if str(predicate).startswith(str(VX)):
            transport.require((predicate, None, None) in vocabulary, 'Undeclared experimental property')
        if predicate == RDF.type and str(obj).startswith(str(VX)):
            transport.require((obj, RDF.type, OWL.Class) in vocabulary, 'Undeclared experimental class')
    transport.require(not list(graph.subjects(RDF.type, KE.HumanAssessment)), 'Human labels prohibited')
    for predicate in (KE.roleConcept, KE.actsOnRepresentation, KE.salaryForRole, KE.compensationBasis,
                      KE.payMarket, KE.internalReviewFlag, OWL.sameAs):
        transport.require(not list(graph.triples((None, predicate, None))), 'Unsupported inferred fact: ' + str(predicate))
    by_hash = {a['sha256']: a for a in packet['captures']}
    artifact_count = 0
    for artifact in graph.subjects(RDF.type, KE.EvidenceArtifact):
        expected = by_hash.get(str(one(graph, artifact, KE.sha256)))
        transport.require(expected is not None, 'Artifact not in authenticated packet')
        transport.require(str(one(graph, artifact, KE.artifactLocation)) == expected['path'], 'Artifact path mismatch')
        data = base64.b64decode(expected['bytes_base64'], validate=True)
        transport.require(transport.digest(data) == expected['sha256'], 'Artifact bytes mismatch')
        artifact_count += 1
    matched = 0
    for p in graph.subjects(RDF.type, KE.EvidencePassage):
        locator = transport.loads(str(one(graph, p, KE.passageLocator)))
        ref = locator['source']; source_value = transport.resolve_reference(packet, ref)
        artifact = one(graph, p, KE.inArtifact)
        transport.require(str(one(graph, artifact, KE.sha256)) == ref['capture_sha256'], 'Passage points to wrong artifact')
        transport.require(str(one(graph, p, VX.sourceValueJSON)) == transport.canonical(source_value), 'Source value mismatch')
        if locator['transform'] == 'json':
            transport.require(locator['pointer'] == ref['pointer'], 'JSON pointer mismatch')
            text = transport.canonical(source_value)
        else:
            text = consumer.resolve_evidence(packet, locator)
        transport.require(str(one(graph, p, KE.passageText)) == text, 'Rendered span/source value mismatch')
        matched += 1
    assertions = 0
    for statement in graph.subjects(RDF.type, VX.SourceAssertion):
        triple = tuple(one(graph, statement, pred) for pred in (RDF.subject, RDF.predicate, RDF.object))
        transport.require(triple in graph, 'Reified source assertion is not asserted')
        refs = list(graph.objects(statement, PROV.wasDerivedFrom))
        transport.require(bool(refs) and all((p, RDF.type, KE.EvidencePassage) in graph for p in refs), 'Unresolved assertion evidence')
        assertions += 1
    runs = list(graph.subjects(RDF.type, VX.GraphBuild))
    transport.require(len(runs) == 1, 'Exactly one build activity required')
    expected = builder.build_graph(packet, consumed, activity=runs[0],
                                   generated_at=one(graph, runs[0], PROV.startedAtTime))
    transport.require(isomorphic(graph, expected), 'Graph facts differ from verified packet/consumer')
    shapes = Graph().parse(builder.HERE / 'shapes_vnext.ttl')
    conforms, violations = shacl(graph, shapes, schema + vocabulary)
    transport.require(conforms, 'Experimental SHACL failed: ' + str(violations))
    # Diagnostic only: original completed-record profile is deliberately unchanged.
    frozen_shapes = Graph().parse(transport.ROOT / 'knowledge-engineering/06-validation/shapes.ttl')
    frozen_conforms, frozen_violations = shacl(graph, frozen_shapes, schema)
    return {'experimental_shacl_conforms': conforms, 'experimental_violations': violations,
            'source_fidelity_passed': True, 'verified_artifacts': artifact_count,
            'resolved_evidence_passages': matched, 'source_assertions': assertions,
            'responsibilities': len(list(graph.subjects(RDF.type, KE.Responsibility))),
            'structured_salary_observations': len(list(graph.subjects(RDF.type, KE.SalaryObservation))),
            'frozen_profile_conforms': frozen_conforms, 'frozen_profile_violations': frozen_violations,
            'frozen_profile_note': 'Legacy locators and mandatory-role completed-record contract; diagnostic only',
            'classification_executed': False}

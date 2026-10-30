"""Separate, reproducible experimental inferences; never alter source-fact RDF."""
import graph_vnext as source
import transport_vnext as t
from rdflib import Graph, Literal, URIRef
from rdflib.compare import isomorphic
from rdflib.namespace import RDF, RDFS, DCTERMS


def build(source_graph, decision):
    graph = Graph()
    items = decision['supporting_evidence'] + decision['core_candidates']
    seen = set()
    for item in items:
        key = t.digest(t.canonical(item).encode())
        if key in seen:
            continue
        seen.add(key)
        loc = item['evidence_locator_json']
        passages = list(source_graph.subjects(source.KE.passageLocator, Literal(loc, datatype=source.XSD.string)))
        t.require(len(passages) == 1, 'Semantic assertion needs one original RDF passage')
        responsibility = URIRef(item['responsibility_id'])
        t.require((responsibility, RDF.type, source.KE.Responsibility) in source_graph, 'Unknown responsibility')
        statement = URIRef('urn:ke-market-observatory:experimental:interpretation:' + key)
        concept = URIRef(item['concept_uri'])
        predicate, obj = DCTERMS.subject, concept
        if item['rule_id'] in ('C1', 'C3'):
            obj = URIRef(str(statement) + ':representation')
            predicate = source.KE.actsOnRepresentation
            graph.add((obj, RDF.type, source.KE.KnowledgeRepresentation))
            graph.add((obj, RDFS.label, Literal(item['representation_text'])))
            graph.add((statement, RDF.value, Literal(item['action'])))
        graph.add((responsibility, predicate, obj))
        graph.add((statement, RDF.type, RDF.Statement))
        for prop, value in ((RDF.subject, responsibility), (RDF.predicate, predicate), (RDF.object, obj),
                            (DCTERMS.subject, concept), (source.PROV.wasDerivedFrom, passages[0]),
                            (source.PROV.wasGeneratedBy, URIRef(item['rule_uri']))):
            graph.add((statement, prop, value))
        graph.add((statement, DCTERMS.description, Literal(item['concept_relation'])))
    return graph


def validate(graph, source_graph, decision):
    t.require(isomorphic(graph, build(source_graph, decision)), 'Semantic assertions differ from source-backed rules')
    return {'valid': True, 'assertions': len(list(graph.subjects(RDF.type, RDF.Statement))),
            'scope': 'Experimental inferred statements, separate from source facts and human approvals'}

"""Conservative explicit ontology/SHACL action grammar; no title or case rules."""
import re

VERB = r'(?:design|build|implement|maintain|create|define|model|develop|integrate|extend|validate|author)'
COORDINATED = VERB + r'(?:(?:,\s*(?:and\s+)?|\s+and\s+)' + VERB + r')*'
SCHEMA = re.compile(r'^(?P<action>'+COORDINATED+r')\s+'
    r'(?:(?:the|our|core|formal|enterprise)\s+|[A-Za-z]+(?:\s+TV)?[\x27’]s\s+)*'
    r'(?P<object>(?:RDF(?:/RDFS)?/OWL\s+)?ontology schemas?|SHACL\s+(?:validation\s+)?(?:shapes|constraints))\b', re.I)
OWNERSHIP = re.compile(r'^(?P<action>own)\s+(?:the\s+)?(?:end-to-end\s+)?'
    r'(?:design|development|versioning)(?:(?:,\s*(?:and\s+)?|\s+and\s+)(?:design|development|versioning))*\s+of\s+'
    r'(?:(?:the|our|core|formal|enterprise)\s+|[A-Za-z]+(?:\s+TV)?[\x27’]s\s+)*'
    r'(?P<object>ontolog(?:y|ies))\b', re.I)

def match(text):
    return OWNERSHIP.match(text) or SCHEMA.match(text)

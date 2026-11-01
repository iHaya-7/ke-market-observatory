"""Current operational global gate; historical G1 decisions remain reproducible."""
import copy
import market_eligibility_vnext as historical
import classify_jobs_vnext as occupational
import consumer_vnext as consumer
import transport_vnext as t
import representation_actions_vnext as actions

VERSION = 'operational-market-title-and-duties-2026-11-01'
POLICY = {**historical.POLICY, 'version': VERSION,
          'G1': 'Outside Saudi Arabia: both a clearly specialized KE occupational title and source-backed substantive KE responsibilities are required.'}

def decide(record, source_type, artifact):
    result = historical.decide(record, source_type, artifact)
    result['policy_version'] = VERSION
    if result['location']['country'] in (None, historical.SA) or result['decision'] != 'Accept':
        return result
    packet = historical.source_projection(record, source_type, artifact)
    try:
        docs = consumer.document_views(packet)
    except t.TransportError as error:
        if str(error) != 'No nonempty body fields': raise
        docs = []
    duties = consumer.extract_responsibilities(packet, docs)
    supports = []
    for duty in duties:
        context = (duty.get('section_metadata') or {}).get('value', '')
        if occupational.CONDITIONAL_CONTEXT.search(context): continue
        for clause, offset in occupational.clauses(duty['text']):
            if occupational.UNSAFE.search(clause): continue
            direct = occupational.DIRECT.match(clause) or actions.match(clause)
            if direct and not occupational.COLLATERAL.match(clause[direct.end():]):
                locator = copy.deepcopy(duty['locator'])
                locator.update(start=locator['start']+offset, end=locator['start']+offset+len(clause))
                t.require(consumer.resolve_evidence(packet, locator) == clause, 'Operational evidence mismatch')
                supports.append(dict(rule='G1', quote=duty['text'], matched_clause=clause, locator=locator))
    result['responsibility_support'] = supports
    result['rule'] = 'G1'
    result['decision'] = 'Accept' if supports else 'Unresolved'
    result['job_market_eligible'] = True if supports else None
    result['reason'] = ('Specialized KE title and explicit source-backed ontology/representation responsibilities.' if supports else
                        'Specialized title present, but substantive KE responsibility support is not established by current extraction/rules; review required.')
    return result

import unittest
import base64
import copy
import transport_vnext as t
from process_experimental_batch import project
import operational_market_vnext as market
from test_market_eligibility_vnext import posting

class OperationalScopeTests(unittest.TestCase):
    def test_board_detail_transport_keeps_native_fields_and_detects_tampering(self):
        board = t.canonical({'jobs':[{'id':123,'title':'Ontology Engineer','location':{'name':'US'}}]}).encode()
        detail = t.canonical({'id':123,'content':'<p>Own ontologies.</p>'}).encode()
        components = [dict(path='learning-local/test/'+str(i),sha256=t.digest(raw),
                           bytes_base64=base64.b64encode(raw).decode(),pointer=pointer)
                      for i,(raw,pointer) in enumerate(((board,'/jobs/0'),(detail,'')))]
        envelope = dict(kind='exact-api-response-envelope-v1',components=components)
        spec=dict(format='greenhouse',source_job_id='123',transport_components=True)
        record,mapping,original = project(spec,t.canonical(envelope).encode())
        self.assertEqual(record['title'],'Ontology Engineer')
        self.assertEqual(mapping['merged_fields']['content']['pointer'],'/content')
        self.assertEqual(mapping['merged_fields']['title']['pointer'],'/jobs/0/title')
        self.assertEqual(len(original['source_records']),2)
        bad=copy.deepcopy(envelope); bad['components'][1]['sha256']='0'*64
        with self.assertRaises(t.TransportError): project(spec,t.canonical(bad).encode())

    def decide(self, **kwargs):
        record, artifact = posting(**kwargs)
        return market.decide(record, 'workable', artifact)

    def test_global_requires_title_and_duty_with_resolvable_support(self):
        body='<h2>Responsibilities</h2><p>Own the design and versioning of our ontologies.</p>'
        accepted=self.decide(title='Senior Ontologist',country='United States',body=body)
        self.assertEqual(accepted['decision'],'Accept')
        self.assertTrue(accepted['responsibility_support'])
        self.assertEqual(self.decide(title='Data Engineer',country='United States',body=body)['decision'],'Reject')
        self.assertEqual(self.decide(title='Ontologist',country='United States',body='')['decision'],'Unresolved')

    def test_qualifications_and_collateral_do_not_supply_duty_support(self):
        for body in ('<h2>Requirements</h2><p>Own ontologies in previous work.</p>',
                     '<h2>Responsibilities</h2><p>Build presentations about ontology design.</p>'):
            self.assertNotEqual(self.decide(title='Ontology Engineer',country='United States',body=body)['decision'],'Accept')

    def test_saudi_scope_is_unchanged(self):
        for text, accepted in [('Design Semantic Layers.',True),('Build ordinary data pipelines.',False)]:
            self.assertEqual(self.decide(body='<h2>Responsibilities</h2><p>'+text+'</p>')['job_market_eligible'],accepted)

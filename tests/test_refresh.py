"""Deterministic adapter and integrity tests; no external network requests."""
import copy
import json
import tempfile
import unittest
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from refresh import canonical, classify, assess_role, experience_info, salary_info, normalize, merge_feed, assemble_records, build_review_queue, validate_market, get_board, refresh
ROOT=Path(__file__).resolve().parents[1]
NOW='2026-10-20T12:00:00Z'

class CollectorTests(unittest.TestCase):
 def test_real_seed_validates(self):
  data=json.loads((ROOT/'data/curated.json').read_text());validate_market(data)
  self.assertTrue(isinstance(data['records'],list))
  # The reference database is editable; no fixed row count or salary assumption.
 def test_nonfinite_salary_max_rejected(self):
  data=json.loads((ROOT/'data/curated.json').read_text());data['records'][0].update(salaryMin=100,salaryMax=float('nan'))
  with self.assertRaises(ValueError):validate_market(data)
 def test_salary_max_without_min_rejected(self):
  data=json.loads((ROOT/'data/curated.json').read_text());data['records'][0].update(salaryMin=None,salaryMax=100)
  with self.assertRaises(ValueError):validate_market(data)
 def test_boolean_salary_rejected(self):
  data=json.loads((ROOT/'data/curated.json').read_text());data['records'][0].update(salaryMin=True,salaryMax=100)
  with self.assertRaises(ValueError):validate_market(data)
 def test_query_id_preserved(self):
  self.assertNotEqual(canonical('https://a.com/job?id=123'),canonical('https://a.com/job?id=456'))
 def test_tracking_removed(self):
  self.assertEqual(canonical('https://jobs.lever.co/x/a/apply?utm_source=tracking'),canonical('https://jobs.lever.co/x/a'))
 def test_linkedin_aliases(self):
  self.assertEqual(canonical('https://sa.linkedin.com/jobs/view/architect-at-company-4480149335/?x=1'),canonical('https://www.linkedin.com/jobs/view/4480149335/'))
 def test_generic_metadata_not_enough(self):
  self.assertIsNone(classify('Office Manager','Maintain document metadata')[0])
 def test_core_title(self):
  self.assertEqual(classify('Junior Knowledge Engineer','Python')[0],'Core KE')
 def test_no_years_not_junior(self):
  got=experience_info('Knowledge Engineer','Hands-on ontology knowledge')
  self.assertIsNone(got['expMin']);self.assertEqual(got['level'],'Not specified')
 def test_contract_not_experience(self):
  got=experience_info('Knowledge Engineer','10-12 months contract; two days per week')
  self.assertIsNone(got['expMin'])
 def test_experience_pattern(self):
  got=experience_info('Engineer','At least 3 years of proven experience in data engineering')
  self.assertEqual(got['expMin'],3)
 def test_explicit_junior(self):
  self.assertEqual(experience_info('Ontology Engineer, Junior','No minimum stated')['level'],'Junior')
 def test_salary_units(self):
  raw={'salaryRange':{'currency':'USD','min':80000,'max':100000,'interval':'per-year'},'salaryDescriptionPlain':'Annual base salary'}
  got=salary_info(raw,'lever','');self.assertTrue(got['salaryEligible']);self.assertEqual(got['period'],'Annual')
 def test_unknown_salary_basis(self):
  raw={'salaryRange':{'currency':'USD','min':80000,'max':100000,'interval':'per-year'}}
  got=salary_info(raw,'lever','');self.assertFalse(got['salaryEligible']);self.assertIsNotNone(got['salaryReview'])
 def test_no_hourly_assumption(self):
  raw={'salaryRange':{'currency':'USD','min':50,'max':70,'interval':'per-hour'}}
  self.assertIsNone(salary_info(raw,'lever','')['salaryMin'])
 def test_greenhouse_cents_and_period(self):
  raw={'pay_input_ranges':[{'currency_type':'USD','min_cents':9000000,'max_cents':11000000,'title':'Annual base salary'}]}
  got=salary_info(raw,'greenhouse','');self.assertEqual(got['salaryMin'],90000);self.assertTrue(got['salaryEligible'])
 def test_greenhouse_no_period(self):
  raw={'pay_input_ranges':[{'currency_type':'USD','min_cents':9000000,'max_cents':11000000,'title':'NYC salary'}]}
  self.assertIsNone(salary_info(raw,'greenhouse','')['salaryMin'])
 def test_no_merged_geographic_bands(self):
  raw={'pay_input_ranges':[{'min_cents':1000000},{'min_cents':2000000}]}
  self.assertIsNone(salary_info(raw,'greenhouse','')['salaryMin'])
 def test_free_text_review(self):
  got=salary_info({},'workable','Base Salary: $90,000 to $100,000')
  self.assertIsNone(got['salaryMin']);self.assertIsNotNone(got['salaryReview'])
 def test_saudi_only_from_location(self):
  raw={'id':'100','text':'Knowledge Engineer','country':'US','categories':{'location':'Seattle'},'hostedUrl':'https://jobs.lever.co/x/100','descriptionPlain':'Working with clients in Saudi Arabia. RDF ontology.'}
  r=normalize(raw,{'id':'s','type':'lever','company':'Example'},NOW)
  self.assertEqual(r['region'],'global')
 def test_workable_saudi_location(self):
  raw={'shortcode':'A123','title':'Ontology Engineer','url':'https://apply.workable.com/x/j/A123/','location':{'country':'SA','city':'Riyadh'},'description':'Ontology, RDF, SHACL','published_on':'2026-10-01'}
  r=normalize(raw,{'id':'s','type':'workable','company':'Example'},NOW)
  self.assertEqual(r['region'],'saudi');self.assertEqual(r['postedAt'],'2026-10-01')
 def test_failed_fetch_preserves_last_seen(self):
  old=[{'id':'x','sourceId':'a','listingStatus':'Open in feed','lastSeenAt':'2026-10-01'}]
  self.assertEqual(merge_feed(old,[],'a',False,NOW),old)
 def test_missing_two_successful_checks(self):
  old=[{'id':'x','sourceId':'a','listingStatus':'Open in feed','lastSeenAt':'2026-10-01'}]
  first=merge_feed(old,[],'a',True,NOW);second=merge_feed(first,[],'a',True,NOW)
  self.assertEqual(first[0]['listingStatus'],'Needs recheck');self.assertEqual(second[0]['listingStatus'],'Not in latest feed');self.assertEqual(second[0]['lastSeenAt'],'2026-10-01')
 def test_first_seen_preserved(self):
  old=[{'id':'x','sourceId':'s','firstSeenAt':'2026-10-01'}]
  new=[{'id':'x','sourceId':'s','firstSeenAt':NOW}]
  self.assertEqual(merge_feed(old,new,'s',True,NOW)[0]['firstSeenAt'],'2026-10-01')
 def test_curated_salary_not_erased(self):
  c=[{'id':'c','sourceUrl':'https://x.com/job/1','salaryMin':80000,'salaryVerifiedAt':'2026-10-01'}]
  a=[{'id':'a','sourceUrl':'https://x.com/job/1','salaryMin':None,'listingStatus':'Open in feed','lastSeenAt':NOW}]
  got=assemble_records(c,a);self.assertEqual(len(got),1);self.assertEqual(got[0]['salaryMin'],80000);self.assertEqual(got[0]['salaryVerifiedAt'],'2026-10-01')
 def test_known_salary_change_updates(self):
  c=[{'id':'c','sourceUrl':'https://x.com/job/1','salaryMin':80000}]
  a=[{'id':'a','sourceUrl':'https://x.com/job/1','salaryMin':90000,'salaryMax':120000,'salaryEligible':True,'salaryBasis':'base','salaryBasisVerified':True,'evidenceType':'employer','currency':'USD','period':'Annual','compensation':'Base salary','salaryVerifiedAt':NOW}]
  self.assertEqual(assemble_records(c,a)[0]['salaryMin'],90000)
 def test_complete_lever_pagination(self):
  calls=[]
  def fetch(url,timeout):
   calls.append(url);return [{'id':str(i)} for i in range(100)] if 'skip=0' in url else []
  rows,w=get_board({'type':'lever','account':'example'},{'maxPages':2},fetch)
  self.assertEqual(len(rows),100);self.assertEqual(len(calls),2)
 def test_truncated_lever_feed_fails(self):
  def fetch(url,timeout):return [{'id':str(i)} for i in range(100)]
  with self.assertRaises(ValueError):get_board({'type':'lever','account':'x'},{'maxPages':1},fetch)
 def test_recruiter_with_many_semantic_keywords_excluded(self):
  decision=assess_role('Associate GTM Recruiter','Design ontologies, RDF, OWL, SHACL and Neo4j knowledge graphs')
  self.assertEqual(decision['decision'],'excluded')
 def test_strong_non_ke_title_match_accepted(self):
  decision=assess_role('Senior Data Engineer','Build ontology models with RDF and SHACL and maintain knowledge graph pipelines')
  self.assertEqual(decision['decision'],'approved');self.assertEqual(decision['relevance'],'Core KE')
 def test_metadata_only_candidate_staged_for_review(self):
  decision=assess_role('Data Governance Specialist','Design metadata management, data catalogs, business glossaries and taxonomies')
  self.assertEqual(decision['decision'],'pending')
 def test_vague_ai_mention_staged_for_review(self):
  decision=assess_role('AI Engineer','The company builds a knowledge graph. Familiar with Neo4j.')
  self.assertEqual(decision['decision'],'pending')
 def test_salary_total_not_base_benchmark(self):
  raw={'salaryRange':{'currency':'USD','min':110000,'max':170000,'interval':'per-year'},'salaryDescriptionPlain':'Annual total compensation / OTE'}
  s=salary_info(raw,'lever','')
  self.assertEqual(s['salaryBasis'],'total');self.assertTrue(s['salaryBasisVerified']);self.assertFalse(s['salaryEligible'])
 def test_salary_ambiguous_held_for_review(self):
  raw={'salaryRange':{'currency':'USD','min':90000,'max':105000,'interval':'per-year'},'salaryDescriptionPlain':'Pay range'}
  s=salary_info(raw,'lever','')
  self.assertEqual(s['salaryBasis'],'unknown');self.assertFalse(s['salaryEligible']);self.assertTrue(s['salaryReview'])
 def test_unverified_pay_cannot_be_flagged_eligible(self):
  data=json.loads((ROOT/'data/curated.json').read_text())
  r=data['records'][0];r.update(salaryEligible=True,salaryBasis='unknown',salaryBasisVerified=False)
  with self.assertRaises(ValueError):validate_market(data)
 def test_no_years_mid_is_not_assumed(self):
  r=experience_info('Data Engineer','Knowledge graph knowledge and ontology experience')
  self.assertEqual(r['level'],'Not specified')
 def test_mid_experience_classification(self):
  r=experience_info('Data Engineer','3 years of experience in ontology engineering')
  self.assertEqual(r['level'],'Mid');self.assertEqual(r['expMin'],3)
 def test_senior_title_with_missing_years(self):
  r=experience_info('Senior Knowledge Engineer','Experience with Neo4j')
  self.assertEqual(r['level'],'Senior');self.assertIsNone(r['expMin'])
 def test_review_queue_stages_unknown_pay_and_status(self):
  curated=[{'id':'c','company':'Employer','title':'Knowledge Engineer','sourceUrl':'https://a.com/job1','evidenceType':'employer','salaryMin':100000,'salaryBasisVerified':False,'region':'global'}]
  automatic=[{'id':'x','company':'Company','title':'Data Governance Specialist','sourceUrl':'https://b.com/job2','roleDecision':'pending','roleReviewReason':'Needs human relevance review','salaryMin':None}]
  queue=build_review_queue(curated,automatic,{'approved':[],'rejected':[]})
  self.assertEqual({x['category'] for x in queue},{'Pay basis','Role relevance'})
 def test_explicitly_rejected_candidate_not_reviewed(self):
  rows=[{'id':'x','company':'C','title':'Data Engineer','sourceUrl':'https://a.com/x','roleDecision':'pending','salaryMin':None}]
  self.assertEqual(build_review_queue([],rows,{'approved':[],'rejected':['x']}),[])
 def test_end_to_end_strict_publish_review_and_salary(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td)
   for folder in ('config','data','public/data'):(root/folder).mkdir(parents=True,exist_ok=True)
   seed=json.loads((ROOT/'data/curated.json').read_text())
   seed['records']=[];seed['reviewQueue']=[]
   (root/'data/curated.json').write_text(json.dumps(seed));(root/'public/data/market.json').write_text(json.dumps(seed))
   (root/'data/auto_records.json').write_text('[]')
   (root/'data/review_decisions.json').write_text('{"approved":[],"rejected":[]}')
   cfg={'sources':[{'id':'lever-test','type':'lever','account':'example','company':'Example','enabled':True}],'fxEnabled':False}
   (root/'config/sources.json').write_text(json.dumps(cfg))
   jobs=[
     {'id':'recruit','text':'Associate GTM Recruiter','hostedUrl':'https://jobs.lever.co/example/recruit',
      'descriptionPlain':'Build RDF OWL ontology and knowledge graph using Neo4j',
      'categories':{'location':'New York'}},
     {'id':'specialist','text':'Knowledge Engineer','hostedUrl':'https://jobs.lever.co/example/specialist',
      'descriptionPlain':'Design ontologies with RDF and SHACL',
      'salaryRange':{'currency':'USD','min':110000,'max':145000,'interval':'per-year'},
      'salaryDescriptionPlain':'Base salary; annual USD','categories':{'location':'New York'}},
     {'id':'adjacent','text':'Data Governance Specialist','hostedUrl':'https://jobs.lever.co/example/adjacent',
      'descriptionPlain':'Design metadata management, business glossary, data catalog, taxonomy',
      'categories':{'location':'New York'}}]
   def fake_fetch(url,timeout):return jobs
   published=refresh(root,fake_fetch)
   self.assertEqual(len(published['records']),1)
   self.assertEqual(published['records'][0]['title'],'Knowledge Engineer')
   self.assertTrue(published['records'][0]['salaryEligible'])
   self.assertEqual(len([q for q in published['reviewQueue'] if q['category']=='Role relevance']),1)
   self.assertEqual(published['reviewQueue'][0]['title'],'Data Governance Specialist')
 def test_full_refresh_failure_retains_records_and_fx(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td)
   for name in ('config','data','public/data'):(root/name).mkdir(parents=True,exist_ok=True)
   seed=json.loads((ROOT/'data/curated.json').read_text())
   (root/'data/curated.json').write_text(json.dumps(seed));(root/'public/data/market.json').write_text(json.dumps(seed));(root/'data/auto_records.json').write_text('[]')
   (root/'config/sources.json').write_text(json.dumps({'sources':[{'id':'test','type':'lever','account':'test','company':'Test','enabled':True}],'fxEnabled':True}))
   def fail(url,timeout):raise OSError('Network unavailable')
   got=refresh(root,fail)
   self.assertEqual(got['records'],seed['records']);self.assertEqual(got['fx']['rates'],seed['fx']['rates']);self.assertEqual(got['sources'][0]['status'],'Check failed');self.assertIsNone(got['meta']['lastSuccessfulCollectionAt'])
 def test_unknown_market_schema_rejected(self):
  with self.assertRaises(ValueError):validate_market({'schemaVersion':99})

if __name__=='__main__':unittest.main()

#!/usr/bin/env python3
"""Collect public ATS postings; preserve evidence, missing values and last-good data.

No browser scraping, LinkedIn cookies, credentials, LLM, or paid API is used.
Only configured board APIs are queried. Free-text pay is held for human review.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import html
import json
import math
import os
from pathlib import Path
import re
import time
from datetime import datetime, timezone
from urllib.error import HTTPError
from urllib.parse import urlsplit, urlunsplit, parse_qs
from urllib.request import Request, urlopen
from concurrent.futures import ThreadPoolExecutor

ROOT = Path(__file__).resolve().parents[1]
ALLOWED_HOSTS = {'api.lever.co','boards-api.greenhouse.io','www.workable.com','apply.workable.com','api.frankfurter.dev','api.frankfurter.app'}
SKILLS = {
 'Knowledge Engineering': r'\bknowledge engineer(?:ing|s)?\b',
 'Knowledge Graph': r'\bknowledge graphs?\b',
 'Ontology': r'\b(?:ontology|ontologies|ontologist)\b',
 'Semantic Layer': r'\bsemantic layers?\b',
 'Semantic Modeling': r'\bsemantic modell?ing\b',
 'Metadata Management': r'\bmetadata management\b',
 'Taxonomy': r'\b(?:taxonomy|taxonomies)\b',
 'Business Glossary': r'\bbusiness glossar(?:y|ies)\b',
 'Data Catalog': r'\bdata catalog(?:ue)?s?\b',
 'RDF': r'\bRDF\b', 'OWL': r'\bOWL\b', 'SPARQL': r'\bSPARQL\b',
 'SHACL': r'\bSHACL\b', 'SKOS': r'\bSKOS\b','Neo4j': r'\bNeo4j\b','GraphRAG': r'\bGraphRAG\b'}

def stamp() -> str:
 return datetime.now(timezone.utc).isoformat(timespec='seconds').replace('+00:00','Z')

def clean(value: object) -> str:
 text = html.unescape(html.unescape(str(value or '')))
 text = re.sub(r'<(?:script|style)\b[^>]*>.*?</(?:script|style)>', ' ', text, flags=re.S|re.I)
 return re.sub(r'\s+', ' ', re.sub(r'<[^>]*>', ' ', text)).strip()

def canonical(url: str) -> str:
 p = urlsplit(url)
 if p.scheme not in ('http','https') or not p.netloc:
  raise ValueError('Invalid source URL')
 if p.hostname and p.hostname.endswith('linkedin.com'):
  match = re.search(r'(\d{8,})', p.path)
  if match:return 'https://www.linkedin.com/jobs/view/' + match.group(1)
 path = p.path.rstrip('/')
 if path.endswith('/apply'):path = path[:-6]
 # Preserve job IDs stored in query strings; do not merge all Accenture/Apple jobs.
 keep = {k:v for k,v in parse_qs(p.query).items() if k.lower() in ('id','jobid','gh_jid','reqid')}
 from urllib.parse import urlencode
 return urlunsplit(('https', p.netloc.lower(), path, urlencode(keep, doseq=True), ''))

def fetch_json(url: str, timeout: int = 20):
 if urlsplit(url).hostname not in ALLOWED_HOSTS:
  raise ValueError('Endpoint is outside the configured public API host allowlist')
 for attempt in range(2):
  try:
   request = Request(url, headers={'User-Agent':'KE-Market-Reference/2.0 (public job-board reader)', 'Accept':'application/json'})
   with urlopen(request, timeout=timeout) as response:
    if urlsplit(response.url).hostname not in ALLOWED_HOSTS:
     raise ValueError('Unexpected redirect host')
    body=response.read(20_000_001)
    if len(body)>20_000_000:raise ValueError('Feed exceeds safe response limit; not treated as complete')
    return json.loads(body)
  except HTTPError as error:
   if error.code not in (429,500,502,503,504) or attempt:raise
   retry=error.headers.get('Retry-After','2')
   pause=int(retry) if str(retry).isdigit() else 2
   if pause>30:raise
   time.sleep(max(2,pause))
 raise RuntimeError('Unreachable fetch state')

def get_board(source: dict, config: dict, fetch=fetch_json) -> tuple[list, list[str]]:
 account=source['account']
 if not re.fullmatch(r'[A-Za-z0-9_-]+',account):raise ValueError('Invalid board account')
 timeout=config.get('httpTimeoutSeconds',20)
 kind=source['type']; warnings=[]
 if kind=='lever':
  jobs=[]; seen=set()
  for page in range(config.get('maxPages',20)):
   batch=fetch(f'https://api.lever.co/v0/postings/{account}?mode=json&limit=100&skip={page*100}',timeout)
   if not isinstance(batch,list):raise ValueError('Unexpected Lever response')
   for job in batch:
    if not isinstance(job,dict) or not job.get('id'):raise ValueError('Malformed Lever record')
    if job['id'] in seen:raise ValueError('Duplicate/repeated API page; feed not complete')
    seen.add(job['id'])
   jobs.extend(batch)
   if len(batch)<100:return jobs,warnings
  raise ValueError('Pagination cap reached; previous data retained')
 if kind=='greenhouse':
  data=fetch(f'https://boards-api.greenhouse.io/v1/boards/{account}/jobs?content=true',timeout)
  if not isinstance(data,dict) or not isinstance(data.get('jobs'),list):raise ValueError('Unexpected Greenhouse response')
  jobs=data['jobs']
  if data.get('meta',{}).get('total',len(jobs))>len(jobs):raise ValueError('Incomplete Greenhouse feed')
  count=0
  for job in jobs:
   if not job.get('id') or not job.get('title'):raise ValueError('Malformed Greenhouse record')
   if classify(job['title'],clean(job.get('content')))[0] and count<config.get('maxDetailsPerBoard',50):
    count+=1
    try:
     details=fetch(f'https://boards-api.greenhouse.io/v1/boards/{account}/jobs/{job["id"]}?pay_transparency=true',timeout)
     if not isinstance(details,dict) or str(details.get('id'))!=str(job['id']):raise ValueError('Invalid detail payload')
     job.update(details)
    except Exception as error:
     job['_detailsUnavailable']=True
     warnings.append(f'Detail request unavailable for {job["id"]}: {type(error).__name__}')
  return jobs,warnings
 if kind=='workable':
  data=fetch(f'https://www.workable.com/api/accounts/{account}?details=true',timeout)
  if not isinstance(data,dict) or not isinstance(data.get('jobs'),list):raise ValueError('Unexpected Workable response')
  jobs=data['jobs']
  if data.get('next') or data.get('next_page'):raise ValueError('Unexpected pagination; adapter review required')
  if any(not isinstance(j,dict) or not j.get('title') or not (j.get('shortcode') or j.get('code') or j.get('id')) for j in jobs):
   raise ValueError('Malformed Workable record')
  return jobs,warnings
 raise ValueError('Unsupported ATS source')

# A domain term mentioned in a job description is not sufficient to count the
# job as Knowledge Engineering. Start with title relevance and then require
# responsibilities with specialized semantic-technology evidence.
CORE_TITLE = re.compile(r'\b(?:knowledge engineer(?:ing)?|knowledge graph engineer|ontology engineer|ontologist|semantic web engineer)\b',re.I)
ADJACENT_TITLE = re.compile(r'\b(?:ai|llm|data|semantic|metadata|ontology|knowledge|graph|information|research|machine learning|ml|solution|enterprise|platform)\b',re.I)
TECHNICAL_ROLE = re.compile(r'\b(?:engineer|architect|scientist|developer|specialist|consultant|model(?:l)?er|technical lead|principal|researcher)\b',re.I)
EXCLUDED_TITLE = re.compile(r'\b(?:recruit(?:er|ing|ment)|talent acquisition|human resources|people operations|sales|business development|marketing|account executive|customer success|gtm|go.to.market|copywriter|graphic designer|internship coordinator)\b',re.I)
SEMANTIC_ACTION = re.compile(r'\b(?:design|build|develop|implement|maintain|model|modelling|modeling|architect|create|curate|validate|engineer|construct|govern|integrate|define)\w*\b',re.I)
ONTOLOGY_EVIDENCE = {'Ontology','Knowledge Graph','RDF','OWL','SPARQL','SHACL','SKOS','GraphRAG','Neo4j'}
META_EVIDENCE = {'Metadata Management','Taxonomy','Business Glossary','Data Catalog','Semantic Layer','Semantic Modeling'}

def assess_role(title: str, text: str) -> dict:
 """Return a conservative machine decision, never a human validation."""
 hay=title+' '+text
 skills=[name for name,pattern in SKILLS.items() if re.search(pattern,hay,re.I)]
 matching=set(skills)
 if EXCLUDED_TITLE.search(title):
  return {'decision':'excluded','relevance':None,'skills':skills,
          'reason':'Non-technical recruiting, HR, sales or marketing title. Keywords in the description do not override this exclusion.'}
 if CORE_TITLE.search(title):
  return {'decision':'approved','relevance':'Core KE','skills':skills,
          'reason':'Explicit Knowledge / Ontology / Knowledge Graph engineering job title.'}
 if not (ADJACENT_TITLE.search(title) and TECHNICAL_ROLE.search(title)):
  if len(matching & ONTOLOGY_EVIDENCE)>=2:
   return {'decision':'pending','relevance':'Applied KG / AI','skills':skills,
           'reason':'Semantic terms occur in the description but the job title is not a confirmed engineering role.'}
  return {'decision':'excluded','relevance':None,'skills':skills,'reason':'No relevant engineering role title.'}
 actions=bool(SEMANTIC_ACTION.search(text))
 core=len(matching & ONTOLOGY_EVIDENCE)
 semantic=len(matching & META_EVIDENCE)
 if not actions:
  if core>=2 or semantic>=2:
   return {'decision':'pending','relevance':'Applied KG / AI','skills':skills,
           'reason':'Relevant technology words are present, but no explicit implementation or modeling responsibility was found.'}
  return {'decision':'excluded','relevance':None,'skills':skills,'reason':'No semantic implementation responsibilities found.'}
 if 'Ontology' in matching and (matching & {'Knowledge Graph','RDF','OWL','SPARQL','SHACL','SKOS','Semantic Modeling'}):
  return {'decision':'approved','relevance':'Core KE','skills':skills,
          'reason':'Related technical title with an ontology and complementary semantic-technology implementation scope.'}
 if 'Knowledge Graph' in matching and ((matching & {'GraphRAG','RDF','OWL','SPARQL','SHACL','Semantic Modeling','Ontology'}) or ('Neo4j' in matching and 'GraphRAG' in matching)):
  return {'decision':'approved','relevance':'Applied KG / AI','skills':skills,
          'reason':'Related technical title with knowledge-graph implementation responsibilities and complementary technology.'}
 if re.search(r'\b(?:metadata|semantic|data (?:architect|model)|information architect)\b',title,re.I) and semantic>=3:
  return {'decision':'pending','relevance':'Metadata / Semantic','skills':skills,
          'reason':'Strong metadata / semantic adjacency, but no explicit ontology or knowledge-graph implementation. Requires manual relevance review.'}
 if core or semantic>=2:
  return {'decision':'pending','relevance':'Applied KG / AI' if core else 'Metadata / Semantic','skills':skills,
          'reason':'Related role mentions semantic concepts, but does not meet the strict automatic acceptance criteria.'}
 return {'decision':'excluded','relevance':None,'skills':skills,'reason':'Insufficient knowledge engineering evidence.'}

def classify(title: str, text: str) -> tuple[str | None,list[str]]:
 """Compatibility helper; pending matches are kept for review, not published."""
 outcome=assess_role(title,text)
 return outcome['relevance'],outcome['skills']

def location_info(raw: dict,kind: str) -> tuple[str,str,str]:
 if kind=='lever':
  loc=raw.get('categories',{}).get('location','');code=raw.get('country','')
 elif kind=='greenhouse':
  loc=(raw.get('location') or {}).get('name','');code=''
 else:
  location=raw.get('location')
  if isinstance(location,dict):
   code=location.get('country_code') or location.get('country') or ''
   loc=location.get('location_str') or ', '.join(str(location.get(k) or '') for k in ('city','country'))
  else:
   code=raw.get('country','');loc=', '.join(str(raw.get(k) or '') for k in ('city','state','country'))
 loc=clean(loc).strip(', ');code=str(code or '').upper()
 if code in ('SA','SAUDI ARABIA') or re.search(r'\b(Saudi Arabia|KSA|Riyadh|Jeddah|Dammam|Khobar|Jubail|Thuwal)\b',loc,re.I):country='Saudi Arabia'
 elif code in ('US','USA','UNITED STATES') or re.search(r'\b(United States|USA|New York|Seattle|San Francisco|Boston|Los Angeles|Washington DC)\b',loc,re.I):country='United States'
 elif code in ('GB','UK','UNITED KINGDOM') or re.search(r'\b(United Kingdom|London|Manchester|Bristol)\b',loc,re.I):country='United Kingdom'
 elif code in ('NL','NETHERLANDS'):country='Netherlands'
 elif code in ('DE','GERMANY'):country='Germany'
 elif code in ('IE','IRELAND'):country='Ireland'
 elif code in ('EG','EGYPT'):country='Egypt'
 elif code in ('AE','UNITED ARAB EMIRATES'):country='United Arab Emirates'
 else:country=loc.split(',')[-1].strip() if ',' in loc else 'Not specified'
 return country,loc or 'Not specified','saudi' if country=='Saudi Arabia' else 'global'

def experience_info(title: str,text: str) -> dict:
 # An exact year value is never inferred from title or employment duration.
 # Title-based seniority may be known even when minimum years remain unspecified.
 patt=r'(?:(?:minimum|at least|over)\s+)?(\d{1,2})\s*(?:[-\u2013]\s*(\d{1,2})|(\+))?\s+years?\s+(?:of\s+)?(?:total\s+|professional\s+|proven\s+|relevant\s+|hands[- ]on\s+)?experience\b'
 match=re.search(patt,text,re.I)
 expr='Not specified';lo=hi=None;basis='No minimum years stated in an unambiguous overall-experience pattern.'
 if match:
  candidate=int(match.group(1));end=int(match.group(2)) if match.group(2) else None
  if 0<=candidate<=60 and (end is None or candidate<=end<=60):
   lo,hi=candidate,end;expr=f'{lo}-{hi} years' if hi is not None else f'{lo}+ years'
   basis='Detected experience wording (verify context): '+match.group(0)
 if re.search(r'\b(junior|entry[- ]level|graduate)\b',title,re.I):level='Junior';source='Explicit junior title.'
 elif re.search(r'\b(senior|sr\.?|lead|principal|staff|director|head of|chief)\b',title,re.I):level='Senior';source='Explicit senior/lead title.'
 elif re.search(r'\bmid[- ]level\b',title,re.I):level='Mid';source='Explicit mid-level title.'
 elif lo is not None and hi is not None and lo<=2 and hi<=2:level='Junior';source='Explicit experience range of 0-2 years.'
 elif lo is not None and lo>=6:level='Senior';source='Explicit experience minimum of 6+ years.'
 elif lo is not None and lo>=2:level='Mid';source='Explicit experience minimum of 2-5 years.'
 else:level='Not specified';source='No reliable seniority evidence.'
 return {'experience':expr,'expMin':lo,'expMax':hi,'level':level,'levelBasis':source+' '+basis}

def salary_info(raw:dict,kind:str,text:str) -> dict:
 result={'salaryMin':None,'salaryMax':None,'currency':None,'period':None,
         'compensation':'Not disclosed','salaryBasis':'none','salaryBasisVerified':False,
         'salaryEligible':False,'salaryReview':None}
 ranges=[]
 if kind=='lever' and isinstance(raw.get('salaryRange'),dict):
  row=raw['salaryRange'];ranges=[{'min':row.get('min'),'max':row.get('max'),'currency':row.get('currency'),
   'interval':row.get('interval'),'title':clean(raw.get('salaryDescriptionPlain') or raw.get('salaryDescription'))}]
 elif kind=='greenhouse' and raw.get('pay_input_ranges'):
  for row in raw['pay_input_ranges']:
   ranges.append({'min':row.get('min_cents')/100 if isinstance(row.get('min_cents'),(int,float)) else None,
    'max':row.get('max_cents')/100 if isinstance(row.get('max_cents'),(int,float)) else None,
    'currency':row.get('currency_type'),'interval':None,
    'title':clean(str(row.get('title',''))+' '+str(row.get('blurb','')))})
 if len(ranges)>1:
  result['salaryReview']='Multiple pay ranges or geographies: review each range individually. No band was inferred.'
  return result
 if ranges:
  row=ranges[0];lo=row['min'];hi=row['max'];label=row['title'];interval=str(row['interval'] or '').lower()
  if not isinstance(lo,(int,float)) or not math.isfinite(lo) or lo<0:return result
  if hi is not None and (not isinstance(hi,(int,float)) or not math.isfinite(hi) or hi<lo):return result
  if interval in ('per-year','year','yearly','annual','annually'):period='Annual'
  elif interval in ('per-month','month','monthly'):period='Monthly'
  elif re.search(r'\b(annual|annually|per year|yearly)\b',label,re.I):period='Annual'
  elif re.search(r'\b(monthly|per month)\b',label,re.I):period='Monthly'
  else:period=None
  currency=str(row['currency'] or '').upper()
  if not period or currency not in ('USD','GBP','EUR','SAR'):
   result['salaryReview']='Structured salary found but period or currency is ambiguous. Conversion is withheld.'
   return result
  # Do not equate pay or salary with *base salary* unless explicitly labelled.
  # Evidence of both base and total in one label is ambiguous; review manually.
  total=bool(re.search(r'\b(total compensation|total remuneration|on[- ]target earnings|OTE|base (?:salary|pay) (?:and|\+) (?:bonus|equity))\b',label,re.I))
  base=bool(re.search(r'\b(base (?:salary|pay|compensation)|salary base|basic salary)\b',label,re.I))
  if total and base:salary_basis='unknown'
  elif total:salary_basis='total'
  elif base:salary_basis='base'
  else:salary_basis='unknown'
  comp={'base':'Base salary','total':'Total compensation / OTE','unknown':'Advertised pay; basis not verified'}[salary_basis]
  verified=salary_basis in ('base','total')
  result.update(salaryMin=lo,salaryMax=hi,currency=currency,period=period,
   compensation=comp,salaryBasis=salary_basis,salaryBasisVerified=verified,
   salaryEligible=verified and salary_basis=='base')
  if not verified:
   result['salaryReview']='Employer advertises a numeric range, but does not explicitly identify base salary versus total compensation. Excluded from base-salary benchmarks.'
 elif re.search(r'(?:\$|USD|GBP|EUR|SAR|\u00a3|\u20ac)\s*\d[\d,.]*',text):
  result['salaryReview']='Potential free-text pay; manual verification of amount, period and base-vs-total is needed.'
 return result

def normalize(raw:dict,source:dict,now:str) -> dict | None:
 kind=source['type'];title=clean(raw.get('text') or raw.get('title'))
 if kind=='lever':
  body=' '.join([clean(raw.get('descriptionPlain') or raw.get('description')),clean(raw.get('additionalPlain')),clean(raw.get('salaryDescriptionPlain') or raw.get('salaryDescription'))]+[clean(x.get('content')) for x in raw.get('lists',[])])
  url=raw.get('hostedUrl');job_id=raw.get('id');posted=None
 elif kind=='greenhouse':
  body=clean(raw.get('content'));url=raw.get('absolute_url');job_id=raw.get('id');posted=raw.get('first_published')
 else:
  body=clean(str(raw.get('description',''))+' '+str(raw.get('full_description','')))
  url=raw.get('url') or raw.get('application_url') or raw.get('shortlink')
  job_id=raw.get('shortcode') or raw.get('code') or raw.get('id');posted=raw.get('published_on')
 assessment=assess_role(title,body)
 if assessment['decision']=='excluded':return None
 relevance,skills=assessment['relevance'],assessment['skills']
 if not url or not job_id:raise ValueError('Matching role missing a durable ID or source URL')
 url=canonical(url)
 country,city,region=location_info(raw,kind)
 salary=salary_info(raw,kind,body);review=salary.pop('salaryReview')
 exp=experience_info(title,body)
 rid='AUTO-'+source['id']+'-'+hashlib.sha256(str(job_id).encode()).hexdigest()[:12]
 summary='Matched terms in the source description: '+', '.join(skills)+'. Review the original role for responsibilities and scope.'
 return {'id':rid,'company':source['company'],'title':title,'country':country,'city':city,'region':region,
  'family':'Knowledge Engineer' if title.lower()=='knowledge engineer' else 'Related title',
  'relevance':relevance,'skills':skills,'roleDecision':assessment['decision'],'roleReviewReason':assessment['reason'],'summary':summary,'notes':'Automatically selected by explicit term rules, not a human fit assessment.',
  'restrictions':'See the original posting; work authorization and clearance are not inferred.',
  **exp,**salary,'evidenceType':'employer','sourceLabel':source['type'].title()+' public job board',
  'sourceUrl':url,'extraUrl':'','evidenceMethod':'Public ATS record; rule-based extraction. No salary estimates.',
  'evidenceDate':now[:10],'salaryVerifiedAt':now if salary['salaryMin'] is not None else None,
  'postedAt':posted,'firstSeenAt':now,'lastSeenAt':now,'listingStatus':'Open in feed',
  'statusNote':'Present in the public job feed at the last successful source check.',
  'collection':'automatic','sourceId':source['id'],'sourceJobId':str(job_id),
  'exactTitle':title.lower()=='knowledge engineer','reviewRequired':bool(review) or assessment['decision']=='pending',
  'reviewReason':review or (assessment['reason'] if assessment['decision']=='pending' else None),
  'missingChecks':0,'origin':'Automatic public ATS collection'}

def merge_feed(old:list,new:list,source_id:str,success:bool,now:str) -> list:
 result={x['id']:copy.deepcopy(x) for x in old}
 present={x['id'] for x in new}
 if not success:return list(result.values())
 for row in new:
  before=result.get(row['id']);row=copy.deepcopy(row)
  if before:row['firstSeenAt']=before.get('firstSeenAt') or now
  result[row['id']]=row
 for rid,row in result.items():
  if row.get('sourceId')==source_id and rid not in present:
   row['missingChecks']=row.get('missingChecks',0)+1
   row['listingStatus']='Not in latest feed' if row['missingChecks']>=2 else 'Needs recheck'
   row['statusNote']='Not seen in a complete successful feed. Last-seen date retained; this is not a confirmed vacancy closure.'
 return list(result.values())

def assemble_records(curated:list,automatic:list) -> list:
 rows=copy.deepcopy(curated); urls={canonical(r['sourceUrl']):i for i,r in enumerate(rows)}
 for auto in automatic:
  key=canonical(auto['sourceUrl'])
  if key not in urls:
   urls[key]=len(rows);rows.append(copy.deepcopy(auto));continue
  row=rows[urls[key]]
  for k in ('listingStatus','statusNote','lastSeenAt','firstSeenAt','sourceId','missingChecks'):
   if k in auto:row[k]=auto[k]
  if auto.get('salaryMin') is not None and auto.get('salaryEligible') and auto.get('salaryBasis')=='base' and auto.get('salaryBasisVerified') and auto.get('evidenceType')=='employer':
   for k in ('salaryMin','salaryMax','currency','period','compensation','salaryEligible','salaryBasis','salaryBasisVerified','salaryVerifiedAt'):
    row[k]=auto[k]
   row['notes']=row.get('notes','')+' Latest explicit base-pay range refreshed from the public ATS.'
  # Human-curated salary/experience evidence is otherwise preserved, never re-dated by a page refresh.
 return rows

def build_review_queue(curated_rows:list,automatic_rows:list,decisions:dict) -> list:
 queue=[]
 approved=set(decisions.get('approved',[]));rejected=set(decisions.get('rejected',[]))
 for row in automatic_rows:
  if row['id'] in rejected:continue
  if row.get('roleDecision','pending')=='pending' and row['id'] not in approved:
   queue.append({'id':row['id'],'category':'Role relevance','company':row['company'],
     'title':row['title'],'sourceUrl':row['sourceUrl'],'reason':row.get('roleReviewReason') or 'Role relevance needs review.'})
  if row.get('salaryMin') is not None and not row.get('salaryBasisVerified'):
   queue.append({'id':row['id'],'category':'Pay basis','company':row['company'],
     'title':row['title'],'sourceUrl':row['sourceUrl'],
     'reason':row.get('reviewReason') or 'Unverified base versus total pay.'})
 for row in curated_rows:
  if row.get('salaryMin') is not None and row.get('evidenceType')=='employer' and not row.get('salaryBasisVerified'):
   queue.append({'id':row['id'],'category':'Pay basis','company':row['company'],
     'title':row['title'],'sourceUrl':row['sourceUrl'],
     'reason':'Historical employer pay range: base versus total compensation is not explicitly verified.'})
  if row.get('region')=='saudi' and row.get('listingStatus') in ('Needs recheck','Listing visible'):
   queue.append({'id':row['id'],'category':'Saudi listing status','company':row['company'],
     'title':row['title'],'sourceUrl':row['sourceUrl'],
     'reason':'Previously observed listing; no current successful source check supports an open status.'})
 # Stable keys deduplicate a salary-review entry if a candidate also entered from a curated record.
 seen=set();out=[]
 for item in queue:
  key=(item['id'],item['category'])
  if key not in seen:seen.add(key);out.append(item)
 return out

def validate_market(data:dict) -> None:
 if data.get('schemaVersion')!=2 or not isinstance(data.get('records'),list):raise ValueError('Invalid market schema')
 ids=set()
 for row in data['records']:
  if not isinstance(row.get('id'),str) or row['id'] in ids:raise ValueError('Duplicate or missing record ID')
  ids.add(row['id']);canonical(row['sourceUrl'])
  for field in ('salaryMin','salaryMax'):
   value=row.get(field)
   if value is not None and (isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or value<0):raise ValueError('Invalid '+field)
  if row.get('salaryMax') is not None and row.get('salaryMin') is None:raise ValueError('Salary maximum without a minimum')
  if row.get('salaryMin') is not None:
   if row.get('salaryMax') is not None and row['salaryMax']<row['salaryMin']:raise ValueError('Invalid salary range')
   if row.get('period') not in ('Annual','Monthly') or row.get('currency') not in ('USD','GBP','EUR','SAR'):raise ValueError('Unsupported pay units')
  if row.get('region')=='saudi' and row.get('country')!='Saudi Arabia':raise ValueError('Saudi location mismatch')
  if row.get('salaryEligible') and not (row.get('evidenceType')=='employer' and row.get('salaryBasis')=='base' and row.get('salaryBasisVerified')):
   raise ValueError('Unverified or non-base salary must not enter employer benchmarks')
 if data['fx']['rates'].get('SAR')!=1:raise ValueError('SAR FX invariant failed')
 for val in data['fx']['rates'].values():
  if not isinstance(val,(int,float)) or not math.isfinite(val) or val<=0:raise ValueError('Invalid FX rate')

def content_hash(records:list) -> str:
 fields=('id','title','company','salaryMin','salaryMax','currency','period','listingStatus','experience','sourceUrl')
 return hashlib.sha256(json.dumps([{k:r.get(k) for k in fields} for r in sorted(records,key=lambda x:x['id'])],sort_keys=True).encode()).hexdigest()[:16]

def atomic_json(path:Path,data:object) -> None:
 path.parent.mkdir(parents=True,exist_ok=True)
 temp=path.with_suffix(path.suffix+'.tmp');temp.write_text(json.dumps(data,indent=2,ensure_ascii=True)+'\n',encoding='utf-8');temp.replace(path)

def refresh(root:Path=ROOT,fetch=fetch_json) -> dict:
 cfg=json.loads((root/'config/sources.json').read_text()); curated=json.loads((root/'data/curated.json').read_text())
 old_path=root/'public/data/market.json';previous=json.loads(old_path.read_text()) if old_path.exists() else copy.deepcopy(curated)
 auto_path=root/'data/auto_records.json';automatic=json.loads(auto_path.read_text()) if auto_path.exists() else []
 decisions_path=root/'data/review_decisions.json'
 decisions=json.loads(decisions_path.read_text()) if decisions_path.exists() else {'approved':[],'rejected':[]}
 now=stamp();payload=copy.deepcopy(curated);meta=payload['meta'];meta.update(copy.deepcopy(previous.get('meta',{})))
 meta['lastAttemptAt']=now
 if os.environ.get('GITHUB_ACTIONS')=='true':
  meta['automationActivated']=True;repo=os.environ.get('GITHUB_REPOSITORY','')
  if re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+',repo):meta['repositoryUrl']='https://github.com/'+repo
 prior_sources={s['id']:s for s in previous.get('sources',[])}
 health=[];success_count=0
 def collect(source):
  status={**source,'status':'Disabled','lastAttemptAt':now,'lastSuccessAt':prior_sources.get(source['id'],{}).get('lastSuccessAt'),'jobCount':None,'matchedCount':None,'error':None}
  if not source.get('enabled'):return source,status,None
  try:
   raw,warnings=get_board(source,cfg,fetch);normalized=[]
   for item in raw:
    row=normalize(item,source,now)
    if row:normalized.append(row)
   status.update(status='OK with warnings' if warnings else 'OK',lastSuccessAt=now,jobCount=len(raw),matchedCount=len(normalized),error='; '.join(warnings)[:1000] or None)
   return source,status,normalized
  except Exception as error:
   status.update(status='Check failed',error=type(error).__name__+': '+str(error)[:350]);return source,status,None
 with ThreadPoolExecutor(max_workers=3) as pool:
  for source,status,new in pool.map(collect,cfg['sources']):
   health.append(status)
   if new is not None:
    success_count+=1;automatic=merge_feed(automatic,new,source['id'],True,now)
 if success_count:meta['lastSuccessfulCollectionAt']=now
 payload['sources']=health
 # Unreviewed adjacent job descriptions never enter the published job and salary dataset.
 approved=set(decisions.get('approved',[]));rejected=set(decisions.get('rejected',[]))
 visible=[]
 for row in automatic:
  if row['id'] in rejected:continue
  if row.get('roleDecision','pending')=='approved' or row['id'] in approved:
   candidate=copy.deepcopy(row)
   if row['id'] in approved:candidate['roleDecision']='approved'
   visible.append(candidate)
 payload['records']=assemble_records(curated['records'],visible)
 payload['reviewQueue']=build_review_queue(payload['records'],automatic,decisions)
 payload['fx']=copy.deepcopy(previous.get('fx',curated['fx']))
 if cfg.get('fxEnabled',True):
  payload['fx']['lastAttemptAt']=now
  try:
   fx=fetch('https://api.frankfurter.dev/v1/latest?base=USD&symbols=GBP,EUR',cfg.get('httpTimeoutSeconds',20))
   if fx.get('base')!='USD' or not fx.get('date'):raise ValueError('Unexpected FX base/date')
   rates=fx['rates'];peg=curated['fx']['usdSar']
   if any(not isinstance(rates.get(k),(int,float)) or rates[k]<=0 for k in ('GBP','EUR')):raise ValueError('Incomplete FX rates')
   payload['fx'].update(rates={'SAR':1,'USD':peg,'GBP':round(peg/rates['GBP'],6),'EUR':round(peg/rates['EUR'],6)},
    date=fx['date'],source='https://frankfurter.dev/',label='Frankfurter reference rates, cross-converted through the configured USD/SAR assumption.',status='Updated',error=None)
  except Exception as error:
   payload['fx'].update(status='Last-good FX retained',error=type(error).__name__+': '+str(error)[:200])
 before={r['id']:r for r in previous['records']};events=[]
 for row in payload['records']:
  old=before.get(row['id'])
  if old is None:events.append({'at':now,'type':'Newly tracked','id':row['id'],'title':row['title'],'company':row['company']})
  elif any(old.get(k)!=row.get(k) for k in ('salaryMin','salaryMax','currency','period')):
   events.append({'at':now,'type':'Salary changed','id':row['id'],'title':row['title'],'company':row['company'],'previousSalaryMin':old.get('salaryMin'),'previousSalaryMax':old.get('salaryMax'),'previousCurrency':old.get('currency'),'previousPeriod':old.get('period')})
  elif old.get('listingStatus')!=row.get('listingStatus'):
   events.append({'at':now,'type':'Source status changed','id':row['id'],'title':row['title'],'company':row['company']})
 def digest(data):
  # Older published review items predate v3 categories; hash them without migration.
  snap={'records':content_hash(data['records']),
        'review':[(r['id'],r.get('category','')) for r in data.get('reviewQueue',[])]}
  return hashlib.sha256(json.dumps(snap,sort_keys=True).encode()).hexdigest()[:16]
 version=digest(payload)
 if version!=digest(previous):meta['lastContentChangeAt']=now
 meta['dataVersion']=version;meta['publishedAt']=now if os.environ.get('GITHUB_ACTIONS')=='true' else meta.get('publishedAt')
 meta['lastRunSummary']={'reviewItems':len(payload['reviewQueue']),'sourcesOK':success_count,'sourcesTotal':sum(bool(s.get('enabled')) for s in cfg['sources']),'newRecords':sum(e['type']=='Newly tracked' for e in events),'changes':len(events)}
 payload['changes']=(events+previous.get('changes',[]))[:150]
 validate_market(payload)
 atomic_json(auto_path,automatic);atomic_json(old_path,payload)
 # Repository commits provide a durable audit trail. Do not archive full descriptions.
 print(json.dumps(meta['lastRunSummary']))
 return payload

if __name__=='__main__':
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--validate-only',action='store_true');args=parser.parse_args()
 if args.validate_only:
  validate_market(json.loads((ROOT/'public/data/market.json').read_text()));print('Market data valid')
 else:refresh()

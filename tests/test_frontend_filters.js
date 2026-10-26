'use strict';
// Synthetic records only: no evaluation corpus, AI labels, or source collection.
const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const vm=require('node:vm');
const source=fs.readFileSync(path.join(__dirname,'../web/app.js'),'utf8');
const copy=value=>JSON.parse(JSON.stringify(value));
function review(outcome='Relevant'){
 return {status:'verified',origin:'human',outcome,reviewer:'Synthetic reviewer (test only)',reviewedAtUtc:'2026-10-20T10:00:00Z',rationale:'Synthetic fixture: explicit representation work is substantiated.',evidence:[{sourceUrl:'https://example.org/test-only',locator:'description paragraph 1 (synthetic)',quote:'Maintain explicit domain concepts, relationships and semantic constraints (test only).'}]};
}
function record(id,title='Knowledge Engineer',options={}){
 const r={id,company:'Synthetic employer (test only)',title,country:'United States',region:'global',city:'Test city',skills:[],level:'Senior',experience:'6+ years',levelBasis:'Synthetic explicit experience passage',summary:'Synthetic fixture only.',sourceUrl:'https://example.org/test-only',evidenceDate:'2026-10-20',evidenceType:'employer',salaryMin:120000,salaryMax:144000,currency:'USD',period:'Annual',salaryBasis:'base',salaryBasisVerified:true,salaryEligible:true,roleDecision:'approved',relevance:'Core KE',listingStatus:'Open in feed',collection:'test',keReview:review(),...options};
 if(r.salaryMin!=null)r.salaryReview={...review('Eligible'),evidence:[{sourceUrl:r.sourceUrl,locator:'salary paragraph 1 (synthetic)',quote:`Synthetic base salary ${r.currency} ${r.salaryMin}-${r.salaryMax} per ${r.period} in the synthetic pay market (test only).`}],employerName:r.company,payMarket:'Synthetic pay market (test only)',country:r.country,observation:{salaryMin:r.salaryMin,salaryMax:r.salaryMax,currency:r.currency,period:r.period}};
 return r;
}
function saudi(id,title,options={}){return record(id,title,{country:'Saudi Arabia',region:'saudi',city:'Riyadh',salaryMin:null,salaryMax:null,currency:null,period:null,salaryEligible:false,salaryBasis:'none',salaryBasisVerified:false,...options});}
function app(records=[],local=false){
 const elements=new Map(),events={};
 function el(selector){
  if(!elements.has(selector))elements.set(selector,{textContent:'',innerHTML:'',hidden:false,disabled:false,dataset:{},classList:{toggle(){}},setAttribute(){},removeAttribute(){},addEventListener(){},showModal(){this.open=true;},close(){this.open=false;}});
  return elements.get(selector);
 }
 const dataset={schemaVersion:2,records:copy(records),sources:[],reviewQueue:[],changes:[],fx:{rates:{SAR:1,USD:3.75,GBP:5,EUR:4.2},date:'2026-10-20'},meta:{automationActivated:false,staleAfterHours:48}};
 el('#seed-data').textContent=JSON.stringify(dataset);
 const document={documentElement:{dataset:{localPreview:String(local)}},querySelector:el,querySelectorAll:()=>[],addEventListener:(type,fn)=>(events[type]??=[]).push(fn),hidden:false};
 const context=vm.createContext({document,location:{protocol:'file:',hash:'#overview',href:'file:///synthetic/index.html'},localStorage:{getItem:()=>null,setItem(){}},window:{addEventListener(){},scrollTo(){},print(){}},history:{replaceState(){}},URL,Intl,Date,console,setTimeout:()=>0,clearTimeout(){},setInterval:()=>0,fetch:()=>{throw Error('Network forbidden in tests');}});
 vm.runInContext(source,context,{filename:'web/app.js'});
 return {context,elements,events,run:code=>vm.runInContext(code,context),value:code=>JSON.parse(JSON.stringify(vm.runInContext(code,context)))};
}
function ids(a,expression){return a.value(expression+'.map(r=>r.id)');}

test('international default includes KE seniority variants, never other occupations or composite titles',()=>{
 const names=['Knowledge Engineer','Senior Knowledge Engineer (IC)','Entry-level Knowledge Engineer','Knowledge Engineer II','Knowledge Engineer, Senior'];
 const rows=names.map((name,n)=>record('ke'+n,name));
 rows.push(record('ontology','Ontology Engineer'),record('kg','Knowledge Graph Engineer'),record('semantic','Semantic Web Engineer'),record('composite','AI Data & Knowledge Engineer'),record('sales','Knowledge Engineer - Sales',{keReview:review('Not relevant')}));
 const a=app(rows);
 assert.deepEqual(ids(a,"filtered('global')"),names.map((_,n)=>'ke'+n));
 assert.equal(a.run('filters.global.occupation'),'knowledge-engineer');
 assert.equal(a.run("titleVariant('Senior Knowledge Engineer - Commercial Sales','Knowledge Engineer')"),false);
 assert.equal(a.run("titleVariant('Knowledge Graph Engineer','Knowledge Engineer')"),false);
});

test('each specialization has its own benchmark and defensive statistics never pool occupations',()=>{
 const a=app([record('ke'),record('ont','Ontology Engineer'),record('kg','Knowledge Graph Engineer'),record('web','Semantic Web Engineer')]);
 for(const [scope,id] of [['ontology-engineer','ont'],['knowledge-graph-engineer','kg'],['semantic-web-engineer','web']]){
  a.context.scope=scope;a.run('filters.global.occupation=scope');
  assert.deepEqual(ids(a,"filtered('global')"),[id]);
  assert.deepEqual(ids(a,'benchmarkRows(market.records)'),[id]);
 }
 assert.doesNotMatch(a.run("filterMarkup('global')"),/data-filter="exact"/);
 assert.doesNotMatch(a.run("filterMarkup('global')").match(/<select id="filter-occupation"[\s\S]*?<\/select>/)[0],/value="all"/);
});

test('computational Ontologist aliases use the ontology specialty only with verified duties',()=>{
 const a=app([record('o','Senior Computational Ontologist'),record('plain','Lead Ontologist'),
  record('unknown','Ontologist',{keReview:undefined}),
  record('unrelated','Ontologist',{keReview:review('Not relevant')}),
  saudi('sa','Computational Ontologist')]);
 assert.deepEqual(ids(a,"filtered('global')"),[]);
 a.run("filters.global.occupation='ontology-engineer'");
 assert.deepEqual(ids(a,"filtered('global')"),['o','plain']);
 assert.deepEqual(ids(a,'benchmarkRows(market.records)'),['o','plain']);
 assert.equal(a.run("saudiCategory(market.records[4])"),'specializations');
 assert.equal(a.run("occupationalScope(market.records[2])"),null);
});

test('research ranges preserve original currency and period instead of unlabeled conversion',()=>{
 const a=app([record('r','Knowledge Engineer',{keReview:undefined,salaryReview:undefined})]);
 const html=a.run('researchRanges()');
 assert.match(html,/USD 120,000–144,000 \/ year/);
 assert.doesNotMatch(html,/37,500/);
});

test('filter change events update category results and counts in both languages',()=>{
 const a=app([saudi('ke','Lead Knowledge Engineer'),saudi('ont','Ontology Engineer'),saudi('other','Data Engineer')]);
 for(const language of ['en','ar']){
  a.context.language=language;a.run("lang=language;filters.saudi.category='all';mount('saudi')");
  assert.match(a.elements.get('#result-count').textContent,/^3 /);
  for(const fn of a.events.change)fn({target:{dataset:{filter:'category'},type:'select-one',value:'specializations'}});
  assert.match(a.elements.get('#result-count').textContent,/^1 /);
  assert.deepEqual(ids(a,"filtered('saudi')"),['ont']);
 }
});

test('other verified specializations are separate named views, not a pooled other bucket',()=>{
 const x=record('x','Semantic governance engineer',{keReview:{...review(),occupation:'other',specialization:'Semantic Governance'}});
 const y=record('y','Domain modeling engineer',{keReview:{...review(),occupation:'other',specialization:'Domain Modeling'}});
 const a=app([x,y]);a.run("filters.global.occupation='other:semantic governance'");
 assert.deepEqual(ids(a,'benchmarkRows(market.records)'),['x']);
 assert.match(a.run("filterMarkup('global')"),/Domain Modeling/);
 assert.doesNotMatch(a.run("filterMarkup('global')"),/<option value="other">/);
});

test('Saudi default includes all three evidenced groups without salary or literal KE title',()=>{
 const a=app([saudi('title','Senior Knowledge Engineer'),saudi('special','Ontology Engineer'),saudi('other','Data Architect'),saudi('bad','Commercial Director',{keReview:review('Not relevant')})]);
 assert.equal(a.run('filters.saudi.category'),'all');assert.equal(a.run('filters.saudi.onlySalary'),false);
 assert.deepEqual(new Set(ids(a,"filtered('saudi')")),new Set(['title','special','other']));
 assert.deepEqual(new Set(a.value("filtered('saudi').map(saudiCategory)")),new Set(['knowledge-engineer','specializations','responsibility-based']));
 for(const [cat,id] of [['knowledge-engineer','title'],['specializations','special'],['responsibility-based','other']]){
  a.context.cat=cat;a.run('filters.saudi.category=cat');assert.deepEqual(ids(a,"filtered('saudi')"),[id]);
 }
});

test('unresolved and legacy machine-approved roles stay outside confirmed Saudi opportunities',()=>{
 const a=app([saudi('yes','Architect'),saudi('pending','Knowledge Engineer',{keReview:review('Insufficient Evidence')}),saudi('legacy','Knowledge Engineer',{keReview:undefined,roleDecision:'approved',relevance:'Core KE'}),saudi('no','Ontology Engineer',{keReview:review('Not relevant')})]);
 assert.deepEqual(ids(a,"filtered('saudi')"),['yes']);
 assert.deepEqual(new Set(ids(a,"reviewRows('saudi')")),new Set(['pending','legacy']));
 a.run("mount('saudi')");const html=a.elements.get('#results').innerHTML;
 assert.match(html,/Saved references awaiting verification/);assert.doesNotMatch(a.run("saudiCards(filtered('saudi'))"),/Knowledge Engineer/);
});

test('AI assessments and evaluation-style fields never become production verified relevance',()=>{
 const ai=saudi('ai','Knowledge Engineer',{keReview:{...review(),origin:'AI'},ai_relevance:'Relevant',ai_role_scope:'Core KE',reviewer_id:'Codex (AI)'});
 const a=app([ai]);assert.deepEqual(ids(a,"filtered('saudi')"),[]);assert.equal(a.run('keStatus(market.records[0])'),'review');
});

test('pay eligibility is independent of role relevance; unrelated eligible pay never enters headlines',()=>{
 const a=app([record('commercial','Commercial Director',{keReview:review('Not relevant')}),record('ke')]);
 assert.equal(a.run('verifiedBasePay(market.records[0])'),true);
 assert.equal(a.run('baseEligible(market.records[0])'),false);
 assert.deepEqual(ids(a,'benchmarkRows(market.records)'),['ke']);
 assert.match(a.run('basisBadge(market.records[0])'),/Base pay verified/);
});

test('old parser flags alone are insufficient for independently verified base-pay headlines',()=>{
 const r=record('legacy');delete r.salaryReview;const a=app([r]);
 assert.equal(a.run('baseEligible(market.records[0])'),false);
 assert.match(a.run("salaryStats(filtered('global'))"),/No eligible base-pay observations/);
});

test('stale amount reviews, missing market/employer, total pay, reposts and AI pay reviews are excluded',()=>{
 const variants=[r=>r.salaryReview.observation.salaryMin++,r=>r.salaryReview.payMarket='',r=>r.salaryReview.payMarket='Not specified',r=>r.salaryReview.employerName='',r=>r.salaryReview.employerName='Unknown',r=>{r.salaryBasis='total';r.salaryEligible=false;},r=>{r.evidenceType='reposted';r.salaryEligible=false;},r=>r.salaryReview.origin='AI',r=>r.salaryReview.evidence=[]];
 for(const mutate of variants){const r=record('r');mutate(r);const a=app([r]);assert.equal(a.run('baseEligible(market.records[0])'),false);}
});

test('missing or unsupported salary units cannot become eligible or be normalized',()=>{
 const a=app([record('r')]);
 for(const [field,value] of [['currency',null],['period',null],['period','Hourly'],['currency','CAD'],['salaryMin',null],['salaryMin',false]]){
  a.context.bad=record('bad');a.context.field=field;a.context.val=value;
  assert.equal(a.run('bad[field]=val; isSalary(bad)'),false);
  assert.equal(a.run('baseEligible(bad)'),false);
 }
});

test('Saudi country cannot leak into international pay when a stale region flag says global',()=>{
 const a=app([record('sa','Knowledge Engineer',{country:'Saudi Arabia',region:'global'}),record('unknown','Knowledge Engineer',{country:'Not specified'})]);
 assert.deepEqual(ids(a,'benchmarkRows(market.records)'),[]);
 assert.deepEqual(ids(a,"filtered('global')"),['unknown']);
 assert.deepEqual(ids(a,"filtered('saudi')"),['sa']);
});

test('unknown and incomplete responsibility reviews are unresolved, not false or verified',()=>{
 for(const change of [r=>r.keReview.evidence=[],r=>r.keReview.evidence[0].locator='',r=>r.keReview.evidence[0].sourceUrl='javascript:alert(1)',r=>r.keReview.reviewer='',r=>r.keReview.reviewedAtUtc='yesterday',r=>r.keReview.status='draft']){
  const r=record('r');change(r);const a=app([r]);assert.equal(a.run('keStatus(market.records[0])'),'review');
 }
});

test('Saudi cards show actual responsibility quotes/provenance and safely escape source text',()=>{
 const r=saudi('r','Systems Architect');r.keReview.evidence[0].quote='<script>test only</script> explicit representation duty';
 const a=app([r]);const html=a.run("saudiCards(filtered('saudi'))");
 assert.match(html,/Responsibility evidence/);assert.match(html,/&lt;script&gt;test only&lt;\/script&gt;/);assert.doesNotMatch(html,/<script>/);
 assert.match(html,/description paragraph 1/);assert.match(html,/Synthetic reviewer/);assert.match(html,/Not disclosed/);
 assert.match(html,/Riyadh · Saudi Arabia/);
});

test('archive handling remains separate from Saudi category and pay requirements',()=>{
 const a=app([saudi('old','Knowledge Engineer',{listingStatus:'Archived / unavailable'}),saudi('now','Data Architect')]);
 assert.deepEqual(ids(a,"filtered('saudi')"),['now']);a.run('filters.saudi.archive=true');
 assert.deepEqual(new Set(ids(a,"filtered('saudi')")),new Set(['old','now']));
});

test('reset restores different international and Saudi defaults through the actual click handler',()=>{
 const a=app([]);a.run("filters.saudi.category='specializations';filters.saudi.onlySalary=true;filters.global.occupation='ontology-engineer'");
 function reset(scope){const button={dataset:{reset:scope}};const target={closest:s=>s.includes('[data-reset]')?button:null};for(const fn of a.events.click)fn({target});}
 reset('saudi');assert.equal(a.run('filters.saudi.category'),'all');assert.equal(a.run('filters.saudi.onlySalary'),false);
 reset('global');assert.equal(a.run('filters.global.occupation'),'knowledge-engineer');
});

test('small samples and empty selections are explicit, never replaced with fabricated salaries',()=>{
 const a=app([record('one')]);assert.match(a.run('salaryStats(market.records)'),/Small reference set/);
 assert.match(a.run('salaryStats([])'),/No eligible base-pay observations/);
 assert.match(a.run('salaryStats([])'),/value mono">—/);assert.doesNotMatch(a.run('salaryStats([])'),/SAR<\/small>0/);
});

test('overview remains the KE default even after selecting a different international specialization',()=>{
 const a=app([record('ke'),record('ont','Ontology Engineer')]);a.run("filters.global.occupation='ontology-engineer';mount('overview')");
 const html=a.elements.get('#view-content').innerHTML;assert.match(html,/data-detail="ke"/);assert.doesNotMatch(html,/data-detail="ont"/);
});

test('Arabic/English preserve Saudi default, evidence labels and RTL layout state',()=>{
 const a=app([saudi('r','Architect')]);a.run("lang='ar';mount('saudi')");
 assert.equal(a.context.document.documentElement.dir,'rtl');assert.match(a.run("filterMarkup('saudi')"),/جميع فرص هندسة المعرفة/);
 assert.match(a.elements.get('#results').innerHTML,/دليل المسؤوليات/);assert.equal(a.run('filters.saudi.category'),'all');
 a.run("lang='en';mount('saudi')");assert.equal(a.context.document.documentElement.dir,'ltr');assert.match(a.elements.get('#results').innerHTML,/Responsibility evidence/);
});

test('CSV export retains original units, occupational scope, pay market and responsibility evidence',()=>{
 const a=app([record('ke'),record('ont','Ontology Engineer')]);a.run("view='global';download=(content,name,type)=>{globalThis.exported={content,name,type};};exportCSV()");
 assert.match(a.context.exported.content,/Pay Market/);assert.match(a.context.exported.content,/Responsibility Evidence/);
 assert.match(a.context.exported.content,/Synthetic pay market/);assert.match(a.context.exported.content,/"Annual"/);assert.doesNotMatch(a.context.exported.content,/"ont"/);
});

test('local preview ignores cached datasets and makes no refresh requests',async()=>{
 const a=app([],true);a.run('refresh(true)');
 assert.match(a.elements.get('#view-content').innerHTML,/Local development preview/);
 assert.match(a.elements.get('#connection-notice').textContent,/no collection or publishing/);
 a.run("lang='ar';mount('saudi')");assert.match(a.elements.get('#view-content').innerHTML,/نسخة تطوير محلية؛ لا جمع بيانات ولا نشر/);
});

test('details retain separate pay-review evidence and manual comparison makes no comparability claim',()=>{
 const a=app([record('ke'),record('ont','Ontology Engineer')]);a.run("details('ke')");
 assert.match(a.elements.get('#detail-body').innerHTML,/Salary evidence/);
 assert.match(a.elements.get('#detail-body').innerHTML,/Synthetic pay market/);
 assert.match(a.elements.get('#detail-body').innerHTML,/Gross\/net basis is not inferred/);
 a.run("selected=new Set(['ke','ont']);compare()");assert.match(a.elements.get('#compare-body').innerHTML,/Currency conversion does not establish comparability/);
});

test('annual USD uses existing FX for monthly SAR while retaining the original annual advertisement',()=>{
 const r=record('annual');const original=copy(r);const a=app([r]);
 assert.equal(a.run('baseEligible(market.records[0])'),true);
 assert.equal(a.run('monthly(market.records[0])'),120000*3.75/12);
 assert.equal(a.run("monthly(market.records[0],'salaryMax')"),45000);
 const table=a.run('salaryTable(market.records)');
 assert.match(table,/37,500–45,000/);
 assert.match(table,/Calculated equivalent · SAR\/month/);
 assert.match(table,/USD 120,000–144,000 \/ year/);
 assert.match(table,/Base pay verified/);
 assert.match(a.run('graph(market.records)'),/USD 120,000–144,000 \/ year/);
 a.run("details('annual')");const detail=a.elements.get('#detail-body').innerHTML;
 assert.match(detail,/120,000 × 3\.75 \/ 12 = 37,500 SAR\/month/);
 assert.match(detail,/USD 120,000–144,000 \/ year/);
 assert.match(detail,/https:\/\/example.org\/test-only/);
 assert.deepEqual(a.value('market.records[0]'),original);
});

test('monthly salaries in supported currencies are never divided by 12 or advertised as originally annual',()=>{
 for(const [currency,rate] of [['USD',3.75],['GBP',5],['EUR',4.2],['SAR',1]]){
  const a=app([record('monthly','Knowledge Engineer',{salaryMin:10000,salaryMax:12000,currency,period:'Monthly'})]);
  assert.equal(a.run('baseEligible(market.records[0])'),true);
  assert.equal(a.run('monthly(market.records[0])'),10000*rate);
  const table=a.run('salaryTable(market.records)');
  assert.ok(table.includes(currency+' 10,000–12,000 / month'));
  assert.doesNotMatch(table,/\/ year|original annual/i);
  a.run("details('monthly')");const detail=a.elements.get('#detail-body').innerHTML;
  assert.doesNotMatch(detail,/\/ 12|\/ year/);
  assert.match(detail,/Calculated equivalent · SAR\/month/);
 }
});

test('unknown currency, unknown period and hourly pay produce no calculated monthly equivalent',()=>{
 for(const [field,value] of [['currency',null],['period',null],['period','Hourly']]){
  const a=app([record('unknown')]);a.context.field=field;a.context.unit=value;
  a.run('market.records[0][field]=unit');
  assert.equal(a.run('monthly(market.records[0])'),null);
  assert.equal(a.run("monthly(market.records[0],'salaryMax')"),null);
  assert.deepEqual(ids(a,'benchmarkRows(market.records)'),[]);
  a.run("details('unknown')");const detail=a.elements.get('#detail-body').innerHTML;
  assert.match(detail,/No salary conversion is calculated/);
  assert.doesNotMatch(detail,/Calculated equivalent|37,500|NaN|Infinity|= .*SAR/);
 }
});

test('mathematically convertible pending pay is labeled for research and cannot affect headlines',()=>{
 const pending=record('pending','Knowledge Engineer',{salaryMin:12000000,salaryMax:14400000,salaryReview:undefined});
 delete pending.salaryReview; // The fixture factory normally supplies an independent synthetic salary review.
 const a=app([record('verified'),pending]);
 assert.equal(a.run('monthly(market.records[1])'),3750000);
 assert.equal(a.run('baseEligible(market.records[1])'),false);
 assert.deepEqual(ids(a,'benchmarkRows(market.records)'),['verified']);
 const stats=a.run('salaryStats(market.records)');assert.match(stats,/37,500/);assert.doesNotMatch(stats,/3,750,000|4,500,000/);
 const chart=a.run('graph(market.records)');assert.match(chart,/data-detail="verified"/);assert.doesNotMatch(chart,/data-detail="pending"/);
 const research=a.run('researchRanges()');assert.match(research,/Unverified \/ Pending Review/);assert.match(research,/USD 12,000,000–14,400,000 \/ year/);
 const table=a.run('salaryTable([market.records[1]])');assert.match(table,/Unverified \/ Pending Review/);assert.match(table,/Excluded from base benchmark/);
 a.run("mount('overview')");assert.match(a.elements.get('#view-content').innerHTML,/Unverified \/ Pending Review/);
});

test('Core KE acceptance and AI joint decisions cannot supply missing salary verification',()=>{
 const core=record('core');delete core.salaryReview;
 const joint=record('joint','Knowledge Engineer',{keReview:{...review(),origin:'AI-Assisted Joint Review — Haya and Lubna'}});
 const noSalary=record('none','Knowledge Engineer',{salaryMin:null,salaryMax:null,currency:null,period:null,salaryBasis:'none',salaryBasisVerified:false,salaryEligible:false});
 const a=app([core,joint,noSalary]);
 assert.equal(a.run("keStatus(market.records[0])"),'confirmed');
 assert.equal(a.run('baseEligible(market.records[0])'),false);
 assert.equal(a.run("keStatus(market.records[1])"),'review');
 assert.deepEqual(ids(a,'benchmarkRows(market.records)'),[]);
 assert.equal(a.run('monthly(market.records[2])'),null);
});

test('a completed ineligible salary review retains its exclusion instead of becoming pending',()=>{
 const r=record('ineligible');r.salaryReview.outcome='Ineligible';
 const a=app([r]);assert.equal(a.run('baseEligible(market.records[0])'),false);
 const badge=a.run('basisBadge(market.records[0])');assert.match(badge,/Excluded from base benchmark/);assert.doesNotMatch(badge,/Pending Review/);
 a.run("details('ineligible')");assert.match(a.elements.get('#detail-body').innerHTML,/Salary evidence/);
});

test('Arabic and English show consistent monthly equivalents, original units and pending status across views',()=>{
 const pending=record('pending','Knowledge Engineer',{period:'Monthly',salaryMin:10000,salaryMax:12000});delete pending.salaryReview;
 const a=app([record('annual','Knowledge Engineer',{level:'Junior'}),pending,saudi('sa','Data Architect',{salaryMin:10000,salaryMax:12000,currency:'USD',period:'Monthly'})]);
 for(const [language,note,status,year,month] of [['en','Calculated equivalent · SAR/month','Unverified / Pending Review','year','month'],['ar','مقابل شهري محسوب · ريال/شهر','غير متحقق / بانتظار المراجعة','سنة','شهر']]){
  a.context.language=language;a.run('lang=language');
  const table=a.run('salaryTable(market.records.slice(0,2))');
  assert.ok(table.includes(note));assert.ok(table.includes(status));assert.ok(table.includes('USD 120,000–144,000 / '+year));assert.ok(table.includes('USD 10,000–12,000 / '+month));assert.match(table,/37,500–45,000/);
  a.run("selected=new Set(['annual','pending']);compare()");const comparison=a.elements.get('#compare-body').innerHTML;assert.ok(comparison.includes(note));assert.ok(comparison.includes(status));
  const cards=a.run('saudiCards([market.records[2]])');assert.ok(cards.includes(note));assert.ok(cards.includes('USD 10,000–12,000 / '+month));
  a.run("mount('junior')");const junior=a.elements.get('#view-content').innerHTML;assert.ok(junior.includes(note));assert.ok(junior.includes('USD 120,000–144,000 / '+year));
  a.run("details('pending')");const detail=a.elements.get('#detail-body').innerHTML;assert.ok(detail.includes(note));assert.ok(detail.includes(status));assert.ok(detail.includes('USD 10,000–12,000 / '+month));
 }
});

'use strict';
const $=(s,r=document)=>r.querySelector(s);
const $$=(s,r=document)=>Array.from(r.querySelectorAll(s));
const esc=x=>String(x??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const number=x=>x==null?'Not disclosed':new Intl.NumberFormat('en-US',{maximumFractionDigits:0}).format(x);
const clone=x=>JSON.parse(JSON.stringify(x));
const validUrl=x=>{try{const u=new URL(x);return ['https:','http:'].includes(u.protocol)?u.href:'#';}catch{return '#';}};
const link=(url,label,cls='')=>`<a class="${cls}" href="${esc(validUrl(url))}" target="_blank" rel="noopener noreferrer">${esc(label)} &nearr;</a>`;
const date=x=>{if(!x)return 'Not recorded';const d=new Date(x.length===10?x+'T12:00:00Z':x);return Number.isNaN(d.getTime())?'Not recorded':d.toLocaleDateString('en-GB',{day:'2-digit',month:'short',year:'numeric'});};
const dateTime=x=>{if(!x)return 'Never';const d=new Date(x);return Number.isNaN(d.getTime())?date(x):d.toLocaleString('en-GB',{timeZone:'Asia/Riyadh',day:'2-digit',month:'short',hour:'2-digit',minute:'2-digit'})+' AST';};
const hoursAgo=x=>x?Math.max(0,(Date.now()-Date.parse(x))/3600000):Infinity;
const SEED=JSON.parse($('#seed-data').textContent);
let market=clone(SEED),view='overview',networkMode='initial',busy=false,toastTimer;
let selected=new Set();
const defaults={q:'',country:'all',level:'all',evidence:'employer',relevance:'all',city:'all',status:'all',exact:false,archive:false,onlySalary:true};
const filters={global:{...defaults},saudi:{...defaults,evidence:'all'},junior:{...defaults}};
const CACHE='ke-market-observatory-v2-last-good';
function validate(data){
 if(!data||data.schemaVersion!==2||!Array.isArray(data.records)||data.records.length>10000||!Array.isArray(data.sources)||!data.meta||!data.fx?.rates)throw Error('Unsupported dataset');
 const ids=new Set();
 for(const r of data.records){
  if(!r||typeof r.id!=='string'||ids.has(r.id)||typeof r.title!=='string'||typeof r.company!=='string'||!Array.isArray(r.skills)||validUrl(r.sourceUrl)==='#')throw Error('Invalid record');
  ids.add(r.id);
  if(r.salaryMin!=null&&(!Number.isFinite(r.salaryMin)||r.salaryMin<0||!['Annual','Monthly'].includes(r.period)||!Number.isFinite(data.fx.rates[r.currency])))throw Error('Invalid salary units');
  if(r.salaryMax!=null&&(!Number.isFinite(r.salaryMax)||r.salaryMax<r.salaryMin))throw Error('Invalid salary range');
 }
 if(data.fx.rates.SAR!==1||Object.values(data.fx.rates).some(v=>!Number.isFinite(v)||v<=0))throw Error('Invalid FX data');
 return data;
}
try{if(location.protocol!=='file:'){const cached=localStorage.getItem(CACHE);if(cached){const c=validate(JSON.parse(cached));if(String(c.meta.lastAttemptAt||'')>String(market.meta.lastAttemptAt||'')){market=c;networkMode='cached';}}}}catch{}
function toast(text){$('#toast').textContent=text;$('#toast').hidden=false;clearTimeout(toastTimer);toastTimer=setTimeout(()=>$('#toast').hidden=true,5500);}
function isSalary(r){return r.salaryMin!=null&&['Annual','Monthly'].includes(r.period)&&Number.isFinite(market.fx.rates[r.currency]);}
function month(r,key='salaryMin'){return isSalary(r)&&r[key]!=null?r[key]*market.fx.rates[r.currency]/(r.period==='Annual'?12:1):null;}
function money(r){if(!isSalary(r))return 'Not disclosed';const lo=month(r),hi=month(r,'salaryMax');return hi==null?'From '+number(lo):lo===hi?number(lo):number(lo)+'\u2013'+number(hi);}
function original(r){if(!isSalary(r))return 'Salary not disclosed / not normalized';let result=r.currency+' '+number(r.salaryMin);if(r.salaryMax!=null&&r.salaryMax!==r.salaryMin)result+='\u2013'+number(r.salaryMax);if(r.salaryMax==null)result='From '+result;return result+' / '+(r.period==='Annual'?'year':'month');}
function employerSample(r){return r.region!=='saudi'&&r.evidenceType==='employer'&&r.salaryEligible&&isSalary(r)&&!/total compensation|OTE/i.test(r.compensation||'');}
function badge(text,color=''){return `<span class="chip ${color}">${esc(text)}</span>`;}
function relevance(r){return badge(r.relevance,r.relevance==='Core KE'?'green':r.relevance==='Applied KG / AI'?'blue':'');}
function evidence(r){return badge(({employer:'Employer disclosure',reposted:'Secondary evidence',estimate:'Salary estimate',user:'Unverified'})[r.evidenceType]||'Source record',r.evidenceType==='employer'?'green':r.evidenceType==='estimate'?'blue':'amber');}
function status(r){
 let text=r.listingStatus||'Needs recheck',color='';
 const src=market.sources.find(s=>s.id===r.sourceId);
 if(text==='Open in feed'){
  if(src?.status==='Check failed'){text='Source check failed';color='amber';}
  else if(hoursAgo(r.lastSeenAt)>market.meta.staleAfterHours){text='Last seen; recheck due';color='amber';}
  else{color='green';}
 }else if(text==='Listing visible'){color='green';}
 else if(text==='Needs recheck')color='amber';
 return badge(text,color);
}
const isArchived=r=>['Archived / unavailable','Not in latest feed'].includes(r.listingStatus);
const freshNew=r=>r.collection==='automatic'&&r.firstSeenAt&&hoursAgo(r.firstSeenAt)<168;
const initials=name=>name.split(/\s+/).filter(Boolean).map(w=>w[0]).slice(0,2).join('').toUpperCase();
function stat(label,value,foot,emph=false){return `<article class="stat${emph?' emph':''}"><div class="label">${esc(label)}</div><div class="value mono">${value}</div><div class="foot">${esc(foot)}</div></article>`;}
function heading(kicker,title,description,note=''){return `<div class="page-heading"><div><span class="eyebrow">${esc(kicker)}</span><h1>${title}</h1><p>${description}</p></div>${note?`<div class="heading-note">${note}</div>`:''}</div>`;}
function sampleStats(rows){const samples=rows.filter(employerSample),mins=samples.map(r=>month(r)),maxs=samples.map(r=>month(r,'salaryMax')).filter(x=>x!=null);return `<div class="stats">${stat('Employer salary references',number(samples.length),'Eligible records in this selection')}${stat('Markets represented',number(new Set(samples.map(r=>r.country)).size),'Country / regional labels, not weighting')}${stat('Lowest advertised floor',mins.length?'<small>SAR</small>'+number(Math.min(...mins)):'&mdash;','Monthly equivalent; not a Junior minimum')}${stat('Highest advertised ceiling',maxs.length?'<small>SAR</small>'+number(Math.max(...maxs)):'&mdash;','Monthly equivalent; not a typical offer',true)}</div>`;}
function renderShell(){
 $('#global-count').textContent=market.records.filter(r=>r.region!=='saudi'&&isSalary(r)).length;
 $('#saudi-count').textContent=market.records.filter(r=>r.region==='saudi').length;
 const meta=market.meta,last=meta.lastSuccessfulCollectionAt;
 const ready=meta.automationActivated&&last&&hoursAgo(last)<=meta.staleAfterHours;
 const local=!['http:','https:'].includes(location.protocol);
 let pill='Prepared snapshot',notice='';
 if(local){pill='Offline preview';notice='Preview only. This file is not a live website. Publish the project to activate server-side collection; the embedded data remains available offline.';}
 else if(networkMode==='failed'){pill='Update unavailable';notice='Could not load a newer dataset. Showing the embedded or last-good cached snapshot; no evidence dates have been changed.';}
 else if(ready){pill='Snapshot connected';notice=`Last successful collection: ${dateTime(last)}. The browser checks the published dataset every 5 minutes; job sources are checked by the daily server workflow.`;}
 else if(meta.automationActivated){pill='Check collection health';notice='The deployment workflow has run, but successful collection is missing or older than 48 hours. Open Sources & updates before treating the listings as current.';}
 else{pill='Not activated';notice='Deployment-ready preview. Daily collection has not been activated. Hosted delivery and scheduled source checks are different things.';}
 $('#sync-pill').textContent=pill;$('#sync-pill').classList.toggle('ok',!!ready&&!local&&networkMode!=='failed');
 $('#connection-notice').textContent=notice;$('#connection-notice').classList.toggle('ok',!!ready&&!local&&networkMode!=='failed');
 $('#side-mode').textContent=ready?'Daily collection configured':'Prepared for deployment';
 $('#footer-evidence').textContent='FX '+date(market.fx.date)+' | Source-level evidence dates retained';
 $$('nav [data-view]').forEach(b=>{b.classList.toggle('active',b.dataset.view===view);if(b.dataset.view===view)b.setAttribute('aria-current','page');else b.removeAttribute('aria-current');});
 $('#crumb-title').textContent=({overview:'OVERVIEW',global:'GLOBAL SALARIES',saudi:'SAUDI ARABIA',junior:'JUNIOR EVIDENCE',sources:'SOURCES & UPDATES'})[view];
 renderTray();
}
function chart(rows){
 rows=rows.filter(employerSample).sort((a,b)=>month(a)-month(b));
 if(!rows.length)return '<div class="empty">No eligible employer salary references in this selection.</div>';
 const ceiling=Math.ceil(Math.max(...rows.map(r=>month(r,'salaryMax')??month(r)))/10000)*10000;
 return `<div class="chart"><div class="chart-legend"><span>0</span><span>${number(ceiling/2)}</span><span>${number(ceiling)} SAR</span></div>${rows.map(r=>{const lo=month(r),hi=month(r,'salaryMax')??lo;return `<div class="chart-row"><button class="text-button chart-role" data-detail="${esc(r.id)}">${esc(r.company)}<small>${esc(r.title)}</small></button><div class="bar-track" role="img" aria-label="${esc(r.company+' monthly range '+money(r)+' SAR')}"><span class="bar-range" style="left:${Math.max(0,lo/ceiling*100)}%;width:${Math.max(.6,(hi-lo)/ceiling*100)}%"></span></div><div class="chart-value mono">${esc(money(r))}</div></div>`;}).join('')}<div class="caption">The chart shows individual advertised ranges, including historical references. It is not a market average, a Saudi salary recommendation, or a Junior salary scale. Single dots indicate a disclosed floor only.</div></div>`;
}
function overview(){
 const salaries=market.records.filter(employerSample),saudi=market.records.filter(r=>r.region==='saudi');
 const sourcesOK=market.sources.filter(s=>['OK','OK with warnings'].includes(s.status)).length;
 $('#view-content').innerHTML=heading('THE VALUE OF CONNECTED KNOWLEDGE','Know the market.<br>Know your value.','A traceable salary benchmark for global Knowledge Engineering roles, alongside the opportunities being advertised in Saudi Arabia.',`<strong>One reference.<br>Two perspectives.</strong>Global compensation<br>Saudi market demand`)
 +`<div class="stats">${stat('Employer salary references',number(salaries.length),'Separate from salary-platform estimates')}${stat('Saudi postings tracked',number(saudi.length),'Includes unverified and archived leads')}${stat('Configured public boards',number(market.sources.length),'Coverage is limited to these sources')}${stat('Sources checked successfully',`${sourcesOK}<small> / ${market.sources.length}</small>`,'Automatic checks; not manual research',true)}</div>`
 +`<div class="overview-grid"><section class="panel"><div class="panel-header"><div><h2>Global salary ranges</h2><p>Gross monthly equivalents in SAR &middot; employer disclosures only</p></div><button class="text-button" data-view="global">Explore &rarr;</button></div>${chart(salaries)}</section><aside class="overview-aside"><section class="hero-card"><span class="eyebrow">NEW &middot; SAUDI ARABIA</span><h2>Where the work<br>is being advertised.</h2><p>Find ontology, knowledge graph and semantic roles &mdash; even when the job title says Architect or Data Engineer.</p><button class="button" data-view="saudi">Explore Saudi opportunities &rarr;</button></section><section class="panel evidence-card"><span class="eyebrow muted">A FAIR COMPARISON</span><h3 style="margin-top:15px">A missing year count<br>does not mean Junior.</h3><p>Experience, salary basis and source status are preserved for every reference. No missing salary is converted into an estimate.</p><div class="thin-rule"></div><button class="text-button" data-view="junior">Read the Junior evidence &rarr;</button><p style="margin:15px 0 0">Review source health before sharing a benchmark with management.</p><button class="text-button" data-view="sources">View update coverage &rarr;</button></section></aside></div>`;
}
function options(items,current){return '<option value="all">All</option>'+[...new Set(items)].filter(Boolean).sort().map(x=>`<option value="${esc(x)}"${x===current?' selected':''}>${esc(x)}</option>`).join('');}
function filterMarkup(scope){
 const f=filters[scope],rows=market.records.filter(r=>scope==='saudi'?r.region==='saudi':r.region!=='saudi');
 return `<section class="filters" aria-label="Filter ${scope} references"><div class="filter-grid"><div class="field"><label for="filter-search">Search company, role or skill</label><input id="filter-search" data-filter="q" type="search" value="${esc(f.q)}" placeholder="Ontology, Neo4j, company..."></div>${scope==='saudi'?`<div class="field"><label for="filter-city">Location</label><select id="filter-city" data-filter="city">${options(rows.map(r=>r.city),f.city)}</select></div><div class="field"><label for="filter-rel">Role relevance</label><select id="filter-rel" data-filter="relevance">${options(rows.map(r=>r.relevance),f.relevance)}</select></div>`:`<div class="field"><label for="filter-country">Country / market</label><select id="filter-country" data-filter="country">${options(rows.map(r=>r.country),f.country)}</select></div><div class="field"><label for="filter-evidence">Evidence type</label><select id="filter-evidence" data-filter="evidence"><option value="all">All evidence types</option><option value="employer"${f.evidence==='employer'?' selected':''}>Employer disclosures</option><option value="reposted"${f.evidence==='reposted'?' selected':''}>Secondary evidence</option><option value="estimate"${f.evidence==='estimate'?' selected':''}>Salary estimates</option></select></div>`}<div class="field"><label for="filter-level">Career level</label><select id="filter-level" data-filter="level">${options(rows.map(r=>r.level),f.level)}</select></div></div><div class="filter-bottom"><div><label class="check-label"><input type="checkbox" data-filter="exact"${f.exact?' checked':''}>Exact title: Knowledge Engineer</label>${scope==='saudi'?`<label class="check-label"><input type="checkbox" data-filter="archive"${f.archive?' checked':''}>Include archived postings</label>`:`<label class="check-label"><input type="checkbox" data-filter="onlySalary"${f.onlySalary?' checked':''}>Disclosed salary only</label>`}<button class="text-button" data-reset="${scope}">Reset</button></div><span class="result-count" id="result-count"></span></div></section>`;
}
function filtered(scope){
 const f=filters[scope];return market.records.filter(r=>{
  if(scope==='saudi'?r.region!=='saudi':r.region==='saudi')return false;
  if(scope==='saudi'&&!f.archive&&isArchived(r))return false;
  if(scope!=='saudi'&&f.onlySalary&&!isSalary(r))return false;
  const hay=[r.company,r.title,r.country,r.city,r.summary,...r.skills].join(' ').toLowerCase();
  return (!f.q||hay.includes(f.q.toLowerCase().trim()))&&(f.country==='all'||r.country===f.country)&&(f.city==='all'||r.city===f.city)&&(f.level==='all'||r.level===f.level)&&(f.relevance==='all'||r.relevance===f.relevance)&&(f.evidence==='all'||r.evidenceType===f.evidence)&&(!f.exact||r.title.trim().toLowerCase()==='knowledge engineer');
 }).sort((a,b)=>scope==='saudi'?({'Core KE':0,'Applied KG / AI':1,'Metadata / Semantic':2}[a.relevance]??3)-({'Core KE':0,'Applied KG / AI':1,'Metadata / Semantic':2}[b.relevance]??3)||a.company.localeCompare(b.company):(month(a)??Infinity)-(month(b)??Infinity));
}
function globalPage(){
 $('#view-content').innerHTML=heading('INTERNATIONAL SALARY BENCHMARK','Global salaries.','Compare source-backed roles by employer, market, experience and monthly salary. Original currencies and evidence remain one click away.')+filterMarkup('global')+'<div id="results"></div>';
 results();
}
function salaryTable(rows){return `<section class="panel"><div class="panel-header"><div><h2>The salary reference set</h2><p>Select up to three roles to compare. Estimates stay separate from employer-based summary statistics.</p></div><button class="button small" data-export="csv">Export CSV &darr;</button></div><div class="table-scroll"><table><thead><tr><th style="width:31%">Role / company</th><th style="width:16%">Market</th><th style="width:17%">Experience</th><th style="width:19%">Monthly SAR</th><th style="width:17%">Evidence</th></tr></thead><tbody>${rows.map(r=>`<tr><td><button class="title-link" data-detail="${esc(r.id)}">${esc(r.title)}</button><span class="subline">${esc(r.company)}</span><span class="subline"><label class="check-label"><input type="checkbox" data-compare="${esc(r.id)}"${selected.has(r.id)?' checked':''}>Compare</label></span></td><td>${esc(r.country)}<span class="subline">${esc(r.city)}</span></td><td>${esc(r.experience)}<span class="subline">${esc(r.level)}</span></td><td><div class="money mono">${esc(money(r))}<small>${esc(original(r))}</small></div><span class="subline">${esc(r.compensation)}</span>${r.reviewRequired?badge('Review pay basis','amber'):''}</td><td>${evidence(r)}<span class="subline">Evidence: ${date(r.salaryVerifiedAt||r.evidenceDate)}</span><button class="text-button" data-detail="${esc(r.id)}" style="font-size:10px;margin-top:8px">Source &amp; details &nearr;</button></td></tr>`).join('')}</tbody></table></div>${!rows.length?'<div class="empty"><strong>No matching references</strong>Change your filters. Missing evidence is not filled with an estimate.</div>':''}</section>`;}
function saudiPage(){
 $('#view-content').innerHTML=heading('LOCAL OPPORTUNITY TRACKER','Knowledge Engineering<br>in Saudi Arabia.','A separate register of Saudi postings: core semantic roles, applied knowledge graph work, and adjacent metadata positions. Not every title is Knowledge Engineer.')+`<div class="notice"><strong>Jobs are not salary benchmarks.</strong> Undisclosed salaries stay blank and are excluded from salary statistics. Saved leads, archived roles and source-verified listings carry different status labels.</div>`+filterMarkup('saudi')+'<div id="results"></div>';
 results();
}
function jobCards(rows){return `<div class="cards-grid">${rows.map(r=>`<article class="job-card"><div class="job-brand"><span class="company-mark">${esc(initials(r.company))}</span><span>${esc(r.company)}</span>${freshNew(r)?badge('Newly tracked','green'):''}</div><h3><button class="title-link" style="font-size:inherit" data-detail="${esc(r.id)}">${esc(r.title)}</button></h3><div class="job-location">${esc(r.city)} &middot; Saudi Arabia</div><div class="chip-row">${relevance(r)}${status(r)}</div><p class="job-summary">${esc(r.summary)}</p><div class="chip-row" style="margin-bottom:14px">${r.skills.slice(0,4).map(s=>badge(s)).join('')}</div><div class="job-facts"><div><small>Experience required</small><strong>${esc(r.experience)}</strong></div><div><small>Monthly salary / SAR</small><strong>${esc(money(r))}</strong></div></div><div class="job-footer">${link(r.sourceUrl,'View original posting','button small')}<button class="text-button" data-detail="${esc(r.id)}">Evidence &amp; notes &rarr;</button></div><div class="job-dates">Published: ${r.postedAt?date(r.postedAt):'Not recorded'} &middot; Evidence: ${date(r.evidenceDate)}${r.lastSeenAt?'<br>Last seen in feed: '+dateTime(r.lastSeenAt):''}${r.duplicateGroup?'<br>Possible description overlap flagged; client identity is not inferred.':''}</div></article>`).join('')}</div>${!rows.length?'<div class="panel empty"><strong>No matching Saudi postings</strong>Try including archived records or broader role labels. No result is not proof that no such job exists in Saudi Arabia.</div>':''}`;}
function results(){
 const rows=filtered(view);$('#result-count').textContent=rows.length+' matching references';
 if(view==='global')$('#results').innerHTML=sampleStats(rows)+salaryTable(rows);
 else{
  const salary=rows.filter(isSalary);const core=rows.filter(r=>r.relevance==='Core KE');const current=rows.filter(r=>r.listingStatus==='Open in feed'&&hoursAgo(r.lastSeenAt)<=market.meta.staleAfterHours&&market.sources.find(s=>s.id===r.sourceId)?.status.startsWith('OK'));
  $('#results').innerHTML=`<div class="stats">${stat('Postings in this view',number(rows.length),'Saved references, not unique hiring requisitions')}${stat('Core KE relevance',number(core.length),'Explicit ontology / semantic responsibilities')}${stat('Feed-confirmed listings',number(current.length),'Confirmed only by a fresh successful API check')}${stat('Salaries disclosed',number(salary.length),'No salary is inferred from international data',true)}</div>`+jobCards(rows);
 }
}
function juniorPage(){
 const rows=market.records.filter(r=>r.region!=='saudi'&&r.level==='Junior'&&isSalary(r));
 $('#view-content').innerHTML=heading('EARLY CAREER / READ CAREFULLY','Junior evidence,<br>without inflated claims.','Only explicitly Junior or entry-level references belong here. A missing experience requirement or an all-level salary range is not evidence of a graduate offer.')+`<div class="notice amber"><strong>This is not a statistically established Junior salary band.</strong> The initial references include one historical job repost and two salary-platform estimates. Sources are not interchangeable; use the original role context.</div><div class="junior-grid">${rows.map(r=>`<article class="panel junior-card">${evidence(r)}<h3>${esc(r.title)}</h3><small>${esc(r.company==='Market estimate'?r.sourceLabel:r.company)} &middot; ${esc(r.country)}</small><div class="junior-money mono">${esc(money(r))}</div><small>SAR per month, gross equivalent</small><p style="margin-top:17px">${esc(r.experience)}<br>${esc(r.compensation)}</p><p>${esc(r.notes)}</p><button class="button small" data-detail="${esc(r.id)}">Read source evidence &nearr;</button></article>`).join('')}</div><section class="panel method-card" style="margin-top:22px"><h2>Compare the scope, then the price</h2><p>Keep geography, actual responsibilities, experience and special restrictions together. Defense-related clearance, specialist industries, taxes and total compensation can change the comparison substantially. A US monthly equivalent is not a recommended Saudi starting salary.</p><button class="text-button" data-view="global">Browse all salary references &rarr;</button></section>`;
}
function sourcesPage(){
 const meta=market.meta,ok=market.sources.filter(s=>s.status.startsWith('OK')).length;
 $('#view-content').innerHTML=heading('TRANSPARENCY BY DESIGN','Sources, freshness<br>and what updates.','The browser reads a shared dataset. A scheduled server workflow collects public job boards, validates the result and publishes a new snapshot. These are separate steps.')+`<div class="stats">${stat('Automatic collection',meta.automationActivated?'Configured':'Not activated','Requires publishing the project to your account')}${stat('Latest successful collection',meta.lastSuccessfulCollectionAt?date(meta.lastSuccessfulCollectionAt):'Never','A browser refresh does not update this date')}${stat('Public board coverage',`${ok}<small> / ${market.sources.length}</small>`,'Sources with successful most recent checks')}${stat('Review queue',number(market.reviewQueue.length),'Ambiguous pay is held out of benchmark statistics',true)}</div><div class="notice${meta.automationActivated?'':' amber'}"><strong>Scope:</strong> ${esc(meta.coverage)} LinkedIn links in saved references are not scraped. Adding a company board requires a supported public feed and a verified account identifier.</div><div class="source-grid">${market.sources.map(s=>`<section class="panel source-card"><div class="source-top"><div><h3>${esc(s.company)}</h3><small>${esc(s.type.toUpperCase())} &middot; ${esc(s.account)}</small></div>${badge(s.status,s.status.startsWith('OK')?'green':s.status==='Check failed'?'amber':'')}</div><p>${esc(s.scope)}</p><div class="source-facts">Last attempt: ${dateTime(s.lastAttemptAt)}<br>Last successful check: ${dateTime(s.lastSuccessAt)}<br>Jobs examined: ${s.jobCount==null?'Not checked':number(s.jobCount)} &middot; Matched: ${s.matchedCount==null?'Not checked':number(s.matchedCount)}</div>${s.error?`<p class="source-error">${esc(s.error)}</p>`:''}${link(s.boardUrl,'Open source board','text-button')}</section>`).join('')}</div>
 <div class="method-grid"><section class="panel method-card"><h2>How the automatic version works</h2><ol><li><strong>Daily collection:</strong> approximately 08:17 Riyadh time, after deployment.</li><li><strong>Source matching:</strong> explicit title and skill rules select related roles; this is not human validation.</li><li><strong>Pay safeguards:</strong> explicit, supported pay periods only. Ambiguous text goes to review.</li><li><strong>Publication:</strong> the updated JSON and HTML are deployed to the same site URL.</li><li><strong>Viewer refresh:</strong> the open dashboard checks for a new snapshot every 5 minutes.</li></ol><p>API failures preserve last-good records. A role missing from two complete checks is marked absent from the feed, not definitively closed. GitHub schedules can be delayed or disabled; the 48-hour stale warning is intentional.</p>${meta.repositoryUrl?link(meta.repositoryUrl+'/actions','Open workflow runs','button small'):'<span class="chip amber">Deployment not connected yet</span>'}</section>
 <section class="panel method-card"><h2>Exchange rates &amp; salary basis</h2><p>Monthly SAR = original salary &times; FX rate ${' / 12 for annual salaries.'} Hourly pay is not annualized without explicit working-time assumptions.</p><div class="code">USD &rarr; SAR ${number(market.fx.rates.USD)}<br>GBP &rarr; SAR ${esc(market.fx.rates.GBP)}<br>EUR &rarr; SAR ${esc(market.fx.rates.EUR)}</div><p>Rate date: ${date(market.fx.date)}<br>Status: ${esc(market.fx.status)}<br>${esc(market.fx.label)}</p><p>${esc(market.fx.usdSarBasis)}</p>${link(market.fx.source,'Open FX source','text-button')}<p style="margin-top:14px">Estimates and reposts never drive employer-only summary statistics. Original salary verification dates do not change when FX rates refresh.</p></section>
 <section class="panel method-card"><h2>Manage one shared reference</h2><p>This online edition is read-only for visitors. The repository is the central source of truth. To add or correct an approved reference, edit <strong>data/curated.json</strong> and publish; to add a feed, edit <strong>config/sources.json</strong>. Do not put private notes, contacts or confidential salary information in a public repository.</p><div class="actions"><button class="button small" data-export="json">Export dataset JSON</button><button class="button small" id="export-all-csv">Export all references CSV</button></div><p style="margin-top:14px">Save copy produces an offline snapshot, not another live deployment. No editing keys or GitHub tokens are placed in this page.</p></section>
 <section class="panel method-card"><h2>What still needs review</h2>${market.reviewQueue.length?market.reviewQueue.slice(0,8).map(r=>`<div class="update-event"><strong>${esc(r.company)} &middot; ${esc(r.title)}</strong><small>${esc(r.reason)}</small>${link(r.sourceUrl,'Review source','text-button')}</div>`).join(''):'<p>No automatic review items have been collected yet. This does not mean all imported references have been reverified.</p>'}<p style="margin-top:14px">Newly tracked is the first observation by this collector, not the original publication date. Potential overlaps between recruiters and employers remain flagged rather than silently merged.</p></section></div>
 <section class="panel method-card"><h2>Latest recorded changes</h2>${market.changes.length?market.changes.slice(0,15).map(c=>`<div class="update-event">${badge(c.type,c.type==='Newly tracked'?'green':'')} <strong>${esc(c.company)} &middot; ${esc(c.title)}</strong><small>${dateTime(c.at)}</small></div>`).join(''):'<p>No automatic changes recorded. This package contains a prepared seed dataset; collection begins only after activation.</p>'}</section>`;
}
function mount(name){
 if(!['overview','global','saudi','junior','sources'].includes(name))name='overview';
 view=name;renderShell();({overview,global:globalPage,saudi:saudiPage,junior:juniorPage,sources:sourcesPage})[view]();
 if(location.hash!=='#'+view){try{history.replaceState(null,'','#'+view);}catch{}}
}
function details(id){
 const r=market.records.find(x=>x.id===id);if(!r)return;
 const conversion=isSalary(r)?`${number(r.salaryMin)}${r.period==='Annual'?' / 12':''} x ${market.fx.rates[r.currency]} = ${number(month(r))} SAR/month`:'No salary conversion is calculated.';
 $('#detail-body').innerHTML=`<h2 class="detail-title" id="detail-heading">${esc(r.title)}</h2><p class="muted">${esc(r.company)} &middot; ${esc(r.city)}, ${esc(r.country)}</p><div class="chip-row">${relevance(r)}${evidence(r)}${status(r)}</div><section class="detail-salary"><small>MONTHLY EQUIVALENT / SAR</small><div class="amount mono">${esc(money(r))}</div><p>${esc(original(r))} &middot; ${esc(r.compensation)}</p><p>${esc(conversion)}<br>FX ${date(market.fx.date)} &middot; Gross, before tax; not a guaranteed offer.</p></section><div class="detail-grid"><div><strong>Experience</strong><p>${esc(r.experience)}<br>${esc(r.levelBasis)}</p></div><div><strong>Role relevance</strong><p>${esc(r.relevance)}<br>${esc(r.collection==='automatic'?'Automatic term match; verify with the original description.':'Curated reference; read the evidence notes.')}</p></div><div class="full"><strong>Scope of the role</strong><p>${esc(r.summary)}</p><div class="chip-row">${r.skills.map(s=>badge(s)).join('')}</div></div><div><strong>Evidence &amp; dates</strong><p>${esc(r.sourceLabel)}<br>Evidence date: ${date(r.evidenceDate)}<br>Salary evidence: ${date(r.salaryVerifiedAt)}<br>Published: ${date(r.postedAt)}<br>First tracked automatically: ${dateTime(r.firstSeenAt)}<br>Last seen in feed: ${dateTime(r.lastSeenAt)}</p></div><div><strong>Source status</strong><p>${esc(r.statusNote||r.listingStatus)}<br>${esc(r.evidenceMethod)}</p></div><div class="full"><strong>Limitations &amp; restrictions</strong><p>${esc(r.notes)}<br>${esc(r.restrictions)}</p>${r.duplicateGroup?'<div class="notice amber">Possible overlapping description. The named recruiter is not proof of the end employer or a separate requisition.</div>':''}${r.reviewRequired?`<div class="notice amber">${esc(r.reviewReason||'Pay composition requires review before comparison.')}</div>`:''}</div></div><h3>Original evidence</h3>${link(r.sourceUrl,r.sourceUrl,'source-url')}${r.extraUrl?link(r.extraUrl,r.extraUrl,'source-url'):''}<div class="actions" style="margin-top:18px">${link(r.sourceUrl,'Open source','button primary')}<button class="button" data-close="detail-dialog">Close</button></div>`;
 $('#detail-dialog').showModal();
}
function renderTray(){selected=new Set([...selected].filter(id=>market.records.some(r=>r.id===id)));$('#compare-tray').hidden=!selected.size;$('#compare-label').textContent=selected.size+' of 3 selected';$('#compare-open').disabled=selected.size<2;}
function compare(){const rows=[...selected].map(id=>market.records.find(r=>r.id===id));if(rows.length<2)return;$('#compare-body').innerHTML=`<div class="compare-columns" style="--n:${rows.length}">${rows.map(r=>`<article class="compare-card">${evidence(r)}<h3>${esc(r.title)}</h3><p>${esc(r.company)}<br>${esc(r.country)}</p><div class="money mono">SAR ${esc(money(r))}</div><p>Monthly equivalent<br>${esc(original(r))}<br>${esc(r.compensation)}</p><strong>EXPERIENCE</strong><p>${esc(r.experience)}<br>${esc(r.level)}</p><strong>ROLE SCOPE</strong><p>${esc(r.summary)}</p><strong>LIMITATIONS</strong><p>${esc(r.notes)}<br>${esc(r.restrictions)}</p>${link(r.sourceUrl,'Original source','text-button')}</article>`).join('')}</div>`;$('#compare-dialog').showModal();}
function download(content,name,type){const url=URL.createObjectURL(new Blob([content],{type}));const a=document.createElement('a');a.href=url;a.download=name;document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),1500);}
function exportCSV(all=false){const rows=all?market.records:['global','saudi'].includes(view)?filtered(view):market.records;const columns=['ID','Company','Job Title','Country','City','Role Relevance','Level','Experience Required','Minimum Years','Maximum Years','Monthly Minimum SAR','Monthly Maximum SAR','Original Salary Minimum','Original Salary Maximum','Currency','Salary Period','Compensation Type','Evidence Type','Evidence Date','Salary Evidence Date','Status','Source URL','Additional Source URL','FX Date','Last Seen In Feed','Source Method'];const data=rows.map(r=>[r.id,r.company,r.title,r.country,r.city,r.relevance,r.level,r.experience,r.expMin,r.expMax,month(r),month(r,'salaryMax'),r.salaryMin,r.salaryMax,r.currency,r.period,r.compensation,r.evidenceType,r.evidenceDate,r.salaryVerifiedAt,r.listingStatus,r.sourceUrl,r.extraUrl,market.fx.date,r.lastSeenAt,r.collection]);const quote=value=>{let s=String(value??'');if(/^[\s]*[=+@-]/.test(s))s="'"+s;return '"'+s.replace(/"/g,'""')+'"';};download('\ufeff'+[columns,...data].map(row=>row.map(quote).join(',')).join('\r\n'),'KE_Market_'+(all?'All':view)+'.csv','text/csv;charset=utf-8');toast('Exported '+rows.length+' references with source URLs.');}
function saveCopy(){const root=document.documentElement.cloneNode(true);root.querySelector('#seed-data').textContent=JSON.stringify(market).replace(/</g,'\\u003c');root.querySelectorAll('dialog').forEach(d=>d.removeAttribute('open'));root.querySelector('#toast').hidden=true;root.querySelector('#compare-tray').hidden=true;download('<!DOCTYPE html>\n'+root.outerHTML,'Knowledge_Engineering_Market_Snapshot.html','text/html;charset=utf-8');toast('Saved an offline snapshot. This copy does not activate a live server.');}
function printView(){let old=$('.print-appendix');if(old)old.remove();const rows=['saudi','global'].includes(view)?filtered(view):view==='junior'?market.records.filter(r=>r.level==='Junior'):market.records;const section=document.createElement('section');section.className='print-appendix';section.innerHTML='<h2>Source appendix</h2>'+rows.map(r=>`<article><strong>${esc(r.company+' | '+r.title)}</strong><div>${esc(original(r))} | SAR ${esc(money(r))}/month | Evidence ${date(r.evidenceDate)}</div>${link(r.sourceUrl,r.sourceUrl,'source-url')}</article>`).join('');$('#view-content').append(section);window.print();}
async function refresh(manual=false){
 if(!['http:','https:'].includes(location.protocol)){if(manual)toast('This is an offline preview. Publish the project to enable the shared data endpoint.');renderShell();return;}
 if(busy)return;busy=true;$('#refresh-data').disabled=true;
 const controller=new AbortController(),timer=setTimeout(()=>controller.abort(),15000);
 try{
  const url=new URL('data/market.json',location.href);url.searchParams.set('t',String(Date.now()));
  const response=await fetch(url,{cache:'no-store',signal:controller.signal,credentials:'same-origin'});
  if(!response.ok)throw Error('HTTP '+response.status);
  const text=await response.text();if(text.length>8_000_000)throw Error('Dataset exceeds size limit');
  const incoming=validate(JSON.parse(text));const changed=JSON.stringify(incoming)!==JSON.stringify(market);
  market=incoming;networkMode='connected';try{localStorage.setItem(CACHE,JSON.stringify(market));}catch{}
  if(changed)mount(view);else renderShell();
  if(manual)toast(changed?'Published snapshot loaded. Source-level dates are unchanged unless the collector verified them.':'Already showing the latest published snapshot. This button does not run the job collector.');
 }catch(error){networkMode='failed';renderShell();if(manual)toast('Update unavailable. Keeping the last readable snapshot.');}
 finally{clearTimeout(timer);busy=false;$('#refresh-data').disabled=false;}
}
document.addEventListener('click',event=>{
 const b=event.target.closest('[data-view],[data-detail],[data-close],[data-export],[data-reset]');
 if(b?.dataset.view){mount(b.dataset.view);window.scrollTo({top:0,behavior:'instant'});}
 if(b?.dataset.detail)details(b.dataset.detail);
 if(b?.dataset.close)$('#'+b.dataset.close).close();
 if(b?.dataset.export==='csv')exportCSV();
 if(b?.dataset.export==='json')download(JSON.stringify(market,null,2),'KE_Market_Dataset.json','application/json');
 if(b?.dataset.reset){filters[b.dataset.reset]={...defaults,evidence:b.dataset.reset==='saudi'?'all':'employer'};mount(view);}
 if(event.target.closest('#export-all-csv'))exportCSV(true);
});
document.addEventListener('input',e=>{if(e.target.dataset.filter==='q'&&filters[view]){filters[view].q=e.target.value;results();}});
document.addEventListener('change',e=>{
 if(e.target.dataset.filter&&e.target.dataset.filter!=='q'&&filters[view]){filters[view][e.target.dataset.filter]=e.target.type==='checkbox'?e.target.checked:e.target.value;results();}
 if(e.target.dataset.compare){const id=e.target.dataset.compare;if(e.target.checked){if(selected.size===3){e.target.checked=false;toast('Select up to three roles.');return;}selected.add(id);}else selected.delete(id);renderTray();}
});
$('#compare-open').addEventListener('click',compare);$('#compare-clear').addEventListener('click',()=>{selected.clear();renderTray();if(view==='global')results();});
$('#save-snapshot').addEventListener('click',saveCopy);$('#refresh-data').addEventListener('click',()=>refresh(true));$('#print-view').addEventListener('click',printView);
$$('dialog').forEach(d=>d.addEventListener('click',e=>{if(e.target===d){const r=d.getBoundingClientRect();if(e.clientX<r.left||e.clientX>r.right||e.clientY<r.top||e.clientY>r.bottom)d.close();}}));
window.addEventListener('hashchange',()=>mount(location.hash.slice(1)));
window.addEventListener('online',()=>refresh());
document.addEventListener('visibilitychange',()=>{if(!document.hidden)refresh();});
setInterval(()=>{if(!document.hidden)refresh();},300000);
validate(market);mount(location.hash.slice(1)||'overview');refresh();

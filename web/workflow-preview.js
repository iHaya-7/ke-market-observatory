/* Local workflow bindings for the EXISTING Observatory application.
   Included only by process_experimental_workflow; never by production build_site. */
function wf(en,ar){return lang==='ar'?ar:en;}
function workflowLabel(value){return ({'Core KE':wf('Core KE','هندسة معرفة أساسية'),'Adjacent Technical':wf('Adjacent Technical','عمل تقني مجاور'),'Insufficient Evidence':wf('Insufficient Evidence','أدلة غير كافية'),'Neither':wf('Neither','لا ينتمي للفئتين')})[value]||value;}
function workflowEvidence(r){
 const occupation=r.occupationalAssessment||{},salary=r.salaryAssessment||{};
 const locator=e=>{const l=typeof e.evidence_locator_json==='string'?JSON.parse(e.evidence_locator_json):e.locator;return l?`${l.source.pointer} · [${l.start}, ${l.end})`:JSON.stringify(e.source||{});};
 const supports=occupation.supporting_evidence||[];
 const observed=occupation.evidence_considered||[];
 return `<section class="panel role-evidence"><h3>${esc(wf('Occupational evidence','الأدلة المهنية'))}</h3><p>${esc(workflowLabel(occupation.proposed_classification||'Not assessed'))} · ${esc((occupation.triggered_rules||[]).join(', '))}</p>`
 +supports.map(e=>`<blockquote dir="auto">${esc(e.matched_clause||e.quote)}</blockquote><p dir="auto">${esc(e.concept?.label||e.concept_uri)} · ${esc(e.concept_relation)}</p><small><code dir="ltr">${esc(locator(e))}</code></small>`).join('')
 +(supports.length?'':`<p>${esc(wf('No occupational conclusion is supported by the implemented rules. Market eligibility is a separate decision.','لا تدعم القواعد الحالية استنتاجاً مهنياً. أهلية السوق قرار مستقل.'))}</p>`)
 +`<ul dir="auto">${(occupation.unresolved_uncertainties||[]).map(s=>`<li>${esc(s)}</li>`).join('')}</ul>`
 +`<details><summary>${esc(wf('All extracted responsibilities','جميع المسؤوليات المستخرجة'))} (${observed.length})</summary>${observed.map(e=>`<blockquote dir="auto">${esc(e.responsibility_text)}</blockquote><small><code dir="ltr">${esc(locator(e))}</code></small>`).join('')}</details></section>`
 +`<section class="panel role-evidence"><h3>${esc(wf('Independent salary evidence','أدلة الراتب المستقلة'))}</h3><p dir="auto">${esc(salary.status||'Not assessed')}</p>`
 +(salary.observations||[]).map(o=>`<p><strong><bdi dir="ltr">${esc(o.lower_amount)}${o.upper_amount==null?'':' – '+esc(o.upper_amount)} ${esc(o.currency||wf('currency unresolved','العملة غير محسومة'))}</bdi> / ${esc(o.period||wf('period unresolved','الفترة غير محسومة'))}</strong><br>${esc(o.compensation_basis==='unknown'?wf('Compensation basis unresolved','أساس التعويض غير محسوم'):o.compensation_basis)} · <bdi dir="auto">${esc(o.pay_market||wf('pay market unresolved','سوق الراتب غير محسوم'))}</bdi></p><p dir="auto">${esc(o.reason)}</p>`
 +(o.normalized?`<p dir="ltr">${esc(num(o.normalized.lower_amount))} – ${esc(num(o.normalized.upper_amount))} SAR/month · FX ${esc(o.normalized.fx_date)} (${esc(o.normalized.rate)})</p>`:'')
 +(o.evidence||[]).map(e=>`<blockquote dir="auto">${esc(e.text||JSON.stringify(o.original))}</blockquote><small><code dir="ltr">${esc(locator(e))}</code></small>`).join('')).join('')
 +(salary.unparsed_signals||[]).map(e=>`<blockquote dir="auto">${esc(e.text)}</blockquote><p dir="auto">${esc(e.reason)}</p><small><code dir="ltr">${esc(locator(e))}</code></small>`).join('')
 +(salary.unhandled_structured_fields||[]).map(e=>`<p dir="auto">${esc(e.reason)} · <code dir="ltr">${esc(e.source.pointer)}</code></p><pre class="code" dir="ltr" style="white-space:pre-wrap">${esc(JSON.stringify(e.value,null,2))}</pre>`).join('')
 +`<p dir="auto">${esc(salary.limitation||'')}</p></section>`
 +`<p><strong>${esc(wf('Production approval: not granted','اعتماد النشر: غير ممنوح'))}</strong><br>${esc(wf('Captured evidence is historical; current listing availability was not rechecked.','الأدلة محفوظة بتاريخ الالتقاط؛ لم يُعَد التحقق من توفر الوظيفة حالياً.'))}</p>`
 +`<details><summary>${esc(wf('Technical provenance and validation','مصدر الأدلة والتحقق التقني'))}</summary><pre class="code" dir="ltr" style="white-space:pre-wrap;overflow-wrap:anywhere">${esc(JSON.stringify({validation:r.workflowValidation,source:r.marketEligibility?.source_capture,sha256:r.marketEligibility?.capture_sha256},null,2))}</pre></details>`;
}
if(DEVELOPMENT_PREVIEW&&seed.developmentPreview?.workflow){
 const priorOriginalPay=originalPay;
 originalPay=function(r){
  const observations=r.salaryAssessment?.observations||[];
  return observations.length?observations.map(o=>`${o.lower_amount??'—'}${o.upper_amount==null?'':' – '+o.upper_amount} ${o.currency||wf('currency unresolved','العملة غير محسومة')} / ${o.period||wf('period unresolved','الفترة غير محسومة')}`).join('; '):priorOriginalPay(r);
 };
 const priorPayRange=payRange;
 payRange=function(r){return isSalary(r)?priorPayRange(r):(r.salaryAssessment?.observations?.length||r.salaryAssessment?.unparsed_signals?.length)?wf('Pay evidence unresolved; see details','أدلة الراتب غير محسومة؛ راجع التفاصيل'):wf('Salary not disclosed','الراتب غير معلن');};
 const priorReview=reviewPage;
 reviewPage=function(){priorReview();const failures=market.processingFailures||[];if(failures.length)$('#view-content').innerHTML+=`<section class="panel"><h2>${esc(wf('Processing failures','حالات تعذر المعالجة'))}</h2>${failures.map(f=>`<h3>${esc(f.title)}</h3><p>${esc(f.error_type)}: ${esc(f.blocker)}</p>`).join('')}</section>`;};
 salaryStats=function(rows){
  const observations=rows.flatMap(r=>(r.salaryAssessment?.observations||[]).filter(o=>o.comparable&&o.normalized&&jobEligible(r)));
  return `<div class="notice">${esc(wf('Local Development salary evidence only — no production approval or population-level claims.','أدلة رواتب تطوير محلية فقط — دون اعتماد نشر أو تعميم على السوق.'))}</div><div class="stats">${st(wf('Comparable base-pay observations','ملاحظات راتب أساسي قابلة للمقارنة'),num(observations.length),wf('Explicit amounts, units, basis and pay market required','تتطلب مبلغاً ووحدة وأساس راتب وسوقاً موثقاً'))}${st(wf('Eligible postings without comparable pay','وظائف مؤهلة دون راتب قابل للمقارنة'),num(rows.filter(r=>!(r.salaryAssessment?.observations||[]).some(o=>o.comparable)).length),wf('Retained as jobs; excluded from salary benchmarks','تظل وظائف مؤهلة وتُستبعد من مؤشرات الرواتب'))}</div>`
   +(!observations.length?`<div class="panel empty">${esc(wf('No verified comparable salary benchmark is available in this sample.','لا يتوفر مؤشر رواتب موثق وقابل للمقارنة في هذه العينة.'))}</div>`:'');
 };
}

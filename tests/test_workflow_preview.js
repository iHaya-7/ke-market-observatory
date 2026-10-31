'use strict';
// Reads only an explicitly generated, local Development workflow preview.
const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const vm=require('node:vm');
const preview=process.env.STAGE7_WORKFLOW_PREVIEW;

function loadPreview(hash='#overview'){
 const html=fs.readFileSync(path.join(preview,'index.html'),'utf8');
 const dataset=JSON.parse(fs.readFileSync(path.join(preview,'data/market.json'),'utf8'));
 const scripts=[...html.matchAll(/<script\b[^>]*>([\s\S]*?)<\/script>/g)].map(m=>m[1]);
 const source=scripts.find(s=>s.includes('function details(id)'));
 assert.ok(source,'Existing Observatory application must be embedded');
 const elements=new Map();
 function el(selector){
  if(!elements.has(selector))elements.set(selector,{textContent:'',innerHTML:'',hidden:false,disabled:false,dataset:{},classList:{toggle(){}},setAttribute(){},removeAttribute(){},addEventListener(){},showModal(){},close(){}});
  return elements.get(selector);
 }
 el('#seed-data').textContent=JSON.stringify(dataset);
 const document={documentElement:{dataset:{localPreview:'true'}},querySelector:el,querySelectorAll:()=>[],addEventListener(){},hidden:false};
 const context=vm.createContext({document,location:{protocol:'file:',hash,href:'file:///development/index.html'+hash},localStorage:{getItem:()=>null,setItem(){}},window:{addEventListener(){},scrollTo(){},print(){}},history:{replaceState(){}},URL,Intl,Date,console,setTimeout:()=>0,clearTimeout(){},setInterval:()=>0,fetch:()=>{throw Error('Network forbidden');}});
 vm.runInContext(source,context);
 return {dataset,el,context};
}

test('direct global entry renders workflow salary evidence before any navigation', {skip:!preview},()=>{
 const {el}=loadPreview('#global');
 assert.ok(el('#results').innerHTML.includes('No verified comparable salary benchmark'));
 assert.ok(el('#results').innerHTML.includes('Comparable base-pay observations'));
});

test('observed salary amounts remain visible when compensation dimensions are unresolved', {skip:!preview},()=>{
 const {dataset,el,context}=loadPreview();
 const rows=dataset.records.filter(r=>r.salaryAssessment.observations.some(o=>o.unresolved_dimensions.length));
 assert.ok(rows.length,'Authentic unresolved salary observations must exercise this regression');
 for(const row of rows){
  const original=vm.runInContext(`originalPay(market.records.find(r=>r.id===${JSON.stringify(row.id)}))`,context);
  assert.ok(!original.includes('Not disclosed'));
  for(const o of row.salaryAssessment.observations){
   assert.ok(original.includes(String(o.lower_amount)));
   if(o.upper_amount!=null)assert.ok(original.includes(String(o.upper_amount)));
   if(o.currency)assert.ok(original.includes(o.currency));
   if(!o.period)assert.ok(original.includes('period unresolved'));
   assert.equal(o.normalized,null);
  }
  vm.runInContext(`details(${JSON.stringify(row.id)})`,context);
  assert.ok(el('#detail-body').innerHTML.includes(original));
 }
});

test('Arabic salary evidence isolates original number order and preserves source direction', {skip:!preview},()=>{
 const {dataset,el,context}=loadPreview();
 const row=dataset.records.find(r=>r.salaryAssessment.observations.length);
 assert.ok(row);
 vm.runInContext(`lang='ar';details(${JSON.stringify(row.id)})`,context);
 const detail=el('#detail-body').innerHTML;
 assert.ok(detail.includes('<bdi dir="ltr">'));
 assert.ok(detail.includes('<blockquote dir="auto">'));
 assert.ok(detail.includes('<ul dir="auto">'));
 assert.ok(detail.includes('أساس التعويض غير محسوم'));
 assert.ok(detail.includes('panel role-evidence'));
});

test('generated workflow preview renders separate assessments without approvals', {skip:!preview},()=>{
 const {dataset,el,context}=loadPreview();
 for(const row of dataset.records){
  vm.runInContext(`details(${JSON.stringify(row.id)})`,context);
  const detail=el('#detail-body').innerHTML;
  assert.ok(detail.includes(row.occupationalAssessment.proposed_classification));
  assert.ok(detail.includes('Production approval: not granted'));
  assert.ok(!detail.includes('Salary eligibility: not evaluated'));
  assert.equal(vm.runInContext(`keStatus(market.records.find(r=>r.id===${JSON.stringify(row.id)}))`,context),'review');
  assert.equal(vm.runInContext(`baseEligible(market.records.find(r=>r.id===${JSON.stringify(row.id)}))`,context),false);
 }
 assert.equal(dataset.meta.automationActivated,false);
 assert.ok(dataset.records.every(r=>r.collection==='development-preview'));
 vm.runInContext("mount('global')",context);
 assert.ok(el('#results').innerHTML.includes('No verified comparable salary benchmark'));
 assert.equal(vm.runInContext("filtered('global').length",context),dataset.records.filter(r=>r.country!=='Saudi Arabia'&&r.marketEligibility.decision==='Accept').length);
 vm.runInContext("mount('saudi')",context);
 assert.equal(vm.runInContext("filtered('saudi').length",context),dataset.records.filter(r=>r.country==='Saudi Arabia'&&r.marketEligibility.decision==='Accept').length);
 vm.runInContext("filters.saudi.q='no-such-posting-token'",context);
 assert.equal(vm.runInContext("filtered('saudi').length",context),0);
 vm.runInContext("market.processingFailures=[{title:'<unsafe>',error_type:'Source error',blocker:'Hash mismatch'}];mount('review')",context);
 assert.ok(el('#view-content').innerHTML.includes('Hash mismatch'));
 assert.ok(el('#view-content').innerHTML.includes('&lt;unsafe&gt;'));
 vm.runInContext("lang='ar';details(market.records[0].id)",context);
 assert.ok(el('#detail-body').innerHTML.includes('الأدلة المهنية'));
 assert.ok(el('#detail-body').innerHTML.includes('اعتماد النشر: غير ممنوح'));
});

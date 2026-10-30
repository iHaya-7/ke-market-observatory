'use strict';
// Reads only an explicitly generated, local Development workflow preview.
const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const vm=require('node:vm');
const preview=process.env.STAGE7_WORKFLOW_PREVIEW;

test('generated workflow preview renders separate assessments without approvals', {skip:!preview},()=>{
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
 const context=vm.createContext({document,location:{protocol:'file:',hash:'#overview',href:'file:///development/index.html'},localStorage:{getItem:()=>null,setItem(){}},window:{addEventListener(){},scrollTo(){},print(){}},history:{replaceState(){}},URL,Intl,Date,console,setTimeout:()=>0,clearTimeout(){},setInterval:()=>0,fetch:()=>{throw Error('Network forbidden');}});
 vm.runInContext(source,context);
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

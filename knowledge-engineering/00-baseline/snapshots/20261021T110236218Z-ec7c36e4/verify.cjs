'use strict';
// Local read-only snapshot verification; no refresh, build, collection or deployment.
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto'),cp=require('node:child_process'),vm=require('node:vm'),assert=require('node:assert/strict');
const {isDeepStrictEqual}=require('node:util');
function sha(bytes) { return crypto.createHash('sha256').update(bytes).digest('hex'); }

function distribution(rows, field) {
  var out = {};
  for (var row of rows) { var key = !Object.hasOwn(row, field) ? '<missing>' : row[field] === null ? '<null>' : String(row[field]); out[key] = (out[key] || 0) + 1; }
  return out;
}

function frontendResults(dataset, predicateSource, validatorSource) {
  var context=vm.createContext({market:JSON.parse(JSON.stringify(dataset)),URL});
  var code=validatorSource+'\n'+predicateSource+'\nvalidate(market); JSON.stringify({eligibleIds:market.records.filter(baseEligible).map(r=>r.id),totalPayIds:market.records.filter(totalEligible).map(r=>r.id),monthlySar:market.records.filter(baseEligible).map(r=>({id:r.id,min:monthly(r),max:monthly(r,"salaryMax")}))});';
  return JSON.parse(vm.runInContext(code,context,{timeout:1000}));
}

function describe(data, predicateSource, validatorSource) {
  var populations = { curated: data.curated.records, automatic: data.automatic, published: data.published.records };
  var evidenceFields = ['sourceUrl','extraUrl','sourceLabel','sourceId','sourceJobId','evidenceType','evidenceMethod','origin','collection','evidenceDate','salaryVerifiedAt','postedAt','firstSeenAt','lastSeenAt','listingStatus','statusNote'];
  var out = { populations: {}, reviewQueue: {}, frontend: frontendResults(data.published, predicateSource, validatorSource), evidenceFields, consistency: {} };
  for (var [name, rows] of Object.entries(populations)) {
    assert(Array.isArray(rows)); var ids = rows.map(r => r.id); assert.equal(new Set(ids).size, ids.length, name + ' duplicate IDs');
    var coverage = {};
    for (var field of evidenceFields) coverage[field] = {
      present: rows.filter(r => Object.hasOwn(r, field)).length,
      nonNull: rows.filter(r => Object.hasOwn(r, field) && r[field] !== null).length,
      nonEmpty: rows.filter(r => Object.hasOwn(r, field) && r[field] != null && (typeof r[field] !== 'string' || r[field].trim() !== '')).length
    };
    out.populations[name] = {
      total: rows.length, roleDecisions: distribution(rows,'roleDecision'), missingRoleDecisionIds: rows.filter(r=>!Object.hasOwn(r,'roleDecision')).map(r=>r.id),
      salaryEligibilityFlags: distribution(rows,'salaryEligible'), numericSalaryMinimum: rows.filter(r=>Number.isFinite(r.salaryMin)).length, salaryBases: distribution(rows,'salaryBasis'),
      evidenceTypes: distribution(rows,'evidenceType'), listingStatuses: distribution(rows,'listingStatus'), evidenceCoverage: coverage,
      validHttpSourceUrls: rows.filter(r => { try { return ['http:','https:'].includes(new URL(r.sourceUrl).protocol); } catch { return false; } }).length,
      missingOrEmptyEvidenceDateIds: rows.filter(r=>r.evidenceDate == null || String(r.evidenceDate).trim()==='').map(r=>r.id)
    };
  }
  var queue = data.published.reviewQueue; assert(Array.isArray(queue));
  var allIds = new Set([...data.curated.records, ...data.automatic].map(r=>r.id));
  var queueKeys = queue.map(q=>JSON.stringify([q.id,q.category]));
  out.reviewQueue = { total:queue.length, byCategory:distribution(queue,'category'), uniqueRecordIds:new Set(queue.map(q=>q.id)).size,
    duplicateIdCategoryPairs:queueKeys.filter((x,i)=>queueKeys.indexOf(x)!==i), unresolvedRecordIds:[...new Set(queue.filter(q=>!allIds.has(q.id)).map(q=>q.id))],
    approvedIds:data.decisions.approved, rejectedIds:data.decisions.rejected, overlappingDecisionIds:data.decisions.approved.filter(id=>data.decisions.rejected.includes(id)) };
  var curatedRobusta=data.curated.records.find(r=>r.id==='SA-004'), autoRobusta=data.automatic.find(r=>r.id==='AUTO-workable-robusta-a033b6913e0c');
  out.consistency = {
    publishedSchemaVersion:data.published.schemaVersion,
    curatedIdsMissingFromPublished:data.curated.records.filter(r=>!data.published.records.some(p=>p.id===r.id)).map(r=>r.id),
    publishedIdsMissingFromInputs:data.published.records.filter(r=>!allIds.has(r.id)).map(r=>r.id),
    publishedSourceIdsWithoutHealth:data.published.records.filter(r=>r.sourceId&&!data.published.sources.some(s=>s.id===r.sourceId)).map(r=>r.id),
    salaryReviewFlagsWithoutQueueIds:data.automatic.filter(r=>r.reviewRequired&&r.salaryMin==null&&!queue.some(q=>q.id===r.id)).map(r=>r.id),
    storedRunReviewCountMatches:data.published.meta.lastRunSummary.reviewItems===queue.length,
    enabledSourceCount:data.published.sources.filter(s=>s.enabled).length,
    storedSuccessfulSourceCount:data.published.sources.filter(s=>s.status.startsWith('OK')).length,
    lastFeedMatchedCount:data.published.sources.reduce((s,r)=>s+(r.matchedCount||0),0),
    knownPossibleDuplicate:{curated:curatedRobusta?{id:curatedRobusta.id,sourceUrl:curatedRobusta.sourceUrl,country:curatedRobusta.country,city:curatedRobusta.city}:null,
      automatic:autoRobusta?{id:autoRobusta.id,sourceUrl:autoRobusta.sourceUrl,country:autoRobusta.country,city:autoRobusta.city}:null,jobToken:'D8EA0BA357',resolved:false}
  };
  return out;
}

function loadData(root) {
  var read = p => JSON.parse(fs.readFileSync(path.join(root,p),'utf8'));
  var data = {curated:read('data/curated.json'),automatic:read('data/auto_records.json'),decisions:read('data/review_decisions.json'),published:read('public/data/market.json')};
  assert(Array.isArray(data.decisions.approved)); assert(Array.isArray(data.decisions.rejected)); return data;
}

function listFiles(root, prefix='') {
  return fs.readdirSync(path.join(root,prefix),{withFileTypes:true}).flatMap(e=>e.isDirectory()?listFiles(root,path.posix.join(prefix,e.name)):[path.posix.join(prefix,e.name)]).sort();
}

function verify(snapshotRoot, repositoryRoot) {
  var manifest = JSON.parse(fs.readFileSync(path.join(snapshotRoot,'manifest.json'),'utf8'));
  var seals = fs.readFileSync(path.join(snapshotRoot,'SHA256SUMS'),'utf8').trim().split('\n').map(line=>{
    var match=/^([a-f0-9]{64})  (.+)$/.exec(line); assert(match,'invalid SHA256SUMS line'); assert(!match[2].includes('..')&&!path.isAbsolute(match[2]),'unsafe seal path');
    assert.equal(sha(fs.readFileSync(path.join(snapshotRoot,match[2]))),match[1],match[2]+' seal mismatch'); return match[2];
  });
  assert.deepEqual(listFiles(snapshotRoot),[...seals,'SHA256SUMS'].sort(),'snapshot inventory differs from seal');
  var data = loadData(snapshotRoot);
  assert.equal(sha(Buffer.from(manifest.frontendEvaluation.predicateSource,'utf8')),manifest.frontendEvaluation.predicateSha256);
  assert.equal(sha(Buffer.from(manifest.frontendEvaluation.validatorSource,'utf8')),manifest.frontendEvaluation.validatorSha256);
  var results = describe(data,manifest.frontendEvaluation.predicateSource,manifest.frontendEvaluation.validatorSource);
  assert.deepEqual(results,manifest.results,'descriptive outputs differ');
  for(var item of manifest.dataFiles) {
    var bytes=fs.readFileSync(path.join(snapshotRoot,item.snapshotPath));
    assert.equal(sha(bytes),item.originalSha256); assert.equal(sha(bytes),item.copySha256); assert.equal(bytes.length,item.bytes);
    if(repositoryRoot) assert(bytes.equals(fs.readFileSync(path.join(repositoryRoot,item.sourcePath))),item.sourcePath+' source bytes differ');
  }
  assert.deepEqual(data.published.meta,manifest.publishedDataset.meta); assert.deepEqual(data.published.fx,manifest.publishedDataset.fx); assert.deepEqual(data.curated.fx,manifest.curatedFx);
  for(var item of manifest.implementationFiles) assert.deepEqual(item,manifest.trackedFilesAtCapture.find(f=>f.path===item.path));
  assert.deepEqual(manifest.publishedHtml,manifest.trackedFilesAtCapture.find(f=>f.path==='public/index.html'));
  if(repositoryRoot) {
    for(var item of manifest.trackedFilesAtCapture) {
      var bytes=fs.readFileSync(path.join(repositoryRoot,item.path)); assert.equal(sha(bytes),item.sha256,item.path+' changed'); assert.equal(bytes.length,item.bytes);
      var blob=cp.execFileSync('git',['cat-file','blob',manifest.git.head+':'+item.path],{cwd:repositoryRoot,maxBuffer:20000000});
      assert.equal(sha(blob),item.headBlobSha256,item.path+' committed blob differs');
      assert.equal(cp.execFileSync('git',['rev-parse',manifest.git.head+':'+item.path],{cwd:repositoryRoot,encoding:'utf8'}).trim(),item.headBlobObjectId);
    }
    assert.equal(cp.execFileSync('git',['rev-parse','HEAD'],{cwd:repositoryRoot,encoding:'utf8'}).trim(),manifest.git.head);
    var html=fs.readFileSync(path.join(repositoryRoot,'public/index.html'),'utf8');
    var match=/<script\b[^>]*\bid=["']seed-data["'][^>]*>([\s\S]*?)<\/script>/i.exec(html); assert(match,'missing embedded seed');
    assert(isDeepStrictEqual(JSON.parse(match[1]),data.published),'dashboard seed differs');
    var js=fs.readFileSync(path.join(repositoryRoot,'web/app.js'),'utf8');
    assert(js.includes(manifest.frontendEvaluation.predicateSource)); for (var part of manifest.frontendEvaluation.validatorParts) assert(js.includes(part));
  }
  return {status:'PASS',snapshotId:manifest.snapshotId,jsonFilesParsed:5,copiedDataFilesVerified:manifest.dataFiles.length,sealedFilesVerified:seals.length,
    trackedSourceFilesVerified:repositoryRoot?manifest.trackedFilesAtCapture.length:0,descriptiveResultsReproduced:true,
    sourceByteComparison:repositoryRoot?'PASS':'not requested; snapshot verification is independent of current repository',
    dashboardComparison:repositoryRoot?'PASS':'capture result recorded in manifest',sha256SumsSha256:sha(fs.readFileSync(path.join(snapshotRoot,'SHA256SUMS')))};
}
const args=process.argv.slice(2);assert(args.length===0||(args.length===2&&args[0]==='--repository'),'Usage: node verify.cjs [--repository PATH]');
console.log(JSON.stringify(verify(__dirname,args.length?path.resolve(args[1]):null),null,2));

'use strict';
/* Market Observatory v3: strict role verification, transparent salary basis, bilingual UI. */
const $=(s,r=document)=>r.querySelector(s);
const $$=(s,r=document)=>Array.from(r.querySelectorAll(s));
const esc=value=>String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const clone=value=>JSON.parse(JSON.stringify(value));
const validUrl=value=>{try{const u=new URL(value);return ['https:','http:'].includes(u.protocol)?u.href:'#';}catch{return '#';}};
const link=(url,label,cls='')=>`<a class="${cls}" href="${esc(validUrl(url))}" target="_blank" rel="noopener noreferrer">${esc(label)} ↗</a>`;
const CACHE='ke-market-observatory-v3-last-good';
const LANG_KEY='ke-market-observatory-language';
let lang='en';
try{lang=localStorage.getItem(LANG_KEY)==='ar'?'ar':'en';}catch{}
/* Interface copy is translatable. Original titles, source URLs, brands and standard
   names remain unchanged. Public source passages are not machine-translated. */
const AR={
 'Knowledge Engineering':'هندسة المعرفة',
 'MARKET OBSERVATORY':'مرصد السوق',
 'THE REFERENCE DESK':'مركز المراجع',
 'Market overview':'نظرة عامة',
 'Global salaries':'الرواتب العالمية',
 'Saudi Arabia':'السعودية',
 'Junior evidence':'مراجع المبتدئين',
 'Sources & updates':'المصادر والتحديثات',
 'Made by Knowledge Engineers Haya & Lubna':'إعداد مهندستَي المعرفة هيا ولبنى',
 'Review queue':'قائمة المراجعة',
 'EVIDENCE OVER ASSUMPTIONS':'الأدلة قبل الافتراضات',
 'Compare the work. Not just the title.':'قارن طبيعة العمل، وليس المسمى فقط.',
 'Public sources only.':'مصادر عامة فقط.',
 'No personal data.':'لا توجد بيانات شخصية.',
 'MARKET INTELLIGENCE':'معلومات السوق',
 'Refresh data':'تحديث البيانات',
 'Save copy':'حفظ نسخة',
 'Knowledge Engineering · Market Observatory':'هندسة المعرفة · مرصد السوق',
 'Print view':'طباعة الصفحة',
 'Compare roles':'مقارنة الوظائف',
 'Clear':'مسح',
 'ROLE & SOURCE RECORD':'تفاصيل الوظيفة والمصدر',
 'Compare the evidence':'مقارنة الأدلة',
 'OVERVIEW':'نظرة عامة',
 'GLOBAL SALARIES':'الرواتب العالمية',
 'SAUDI ARABIA':'السعودية',
 'JUNIOR EVIDENCE':'مراجع المبتدئين',
 'SOURCES & UPDATES':'المصادر والتحديثات',
 'REVIEW QUEUE':'قائمة المراجعة',
 'Prepared for deployment':'جاهز للنشر',
 'Daily collection configured':'التحديث اليومي مهيأ',
 'Offline preview':'معاينة دون اتصال',
 'Update unavailable':'التحديث غير متاح',
 'Snapshot connected':'البيانات متصلة',
 'Check collection health':'راجع حالة جمع البيانات',
 'Not activated':'لم يتم التفعيل',
 'This preview is not a live site. Data collection activates after deployment.':'هذه معاينة غير متصلة؛ يبدأ جمع البيانات بعد النشر.',
 'Showing the embedded or last saved snapshot because the update failed.':'نعرض آخر نسخة متاحة لأن تحديث البيانات تعذر.',
 'Last successful collection':'آخر جمع ناجح',
 'The browser checks published data every 5 minutes; the scheduled workflow checks sources daily.':'تفحص الصفحة البيانات المنشورة كل خمس دقائق؛ ويفحص النظام المصادر يوميًا.',
 'The last successful collection is missing or stale. Verify the source status.':'آخر جمع ناجح غير متاح أو قديم؛ تحقق من حالة المصادر.',
 'Daily collection has not been activated.':'التحديث اليومي لم يتم تفعيله بعد.',
 'Source-level evidence dates retained':'تواريخ أدلة المصادر محفوظة',
 'Not disclosed':'غير معلن',
 'Not specified':'غير محدد',
 'Not recorded':'غير مسجل',
 'Never':'لم يحدث',
 'From':'ابتداءً من',
 'year':'سنة',
 'month':'شهر',
 'years':'سنوات',
 'Annual':'سنوي',
 'Monthly':'شهري',
 'Junior':'مبتدئ',
 'Mid':'متوسط الخبرة',
 'Senior':'متقدم',
 'Core KE':'هندسة معرفة أساسية',
 'Applied KG / AI':'معرفة مترابطة وذكاء اصطناعي',
 'Metadata / Semantic':'بيانات وصفية ونمذجة دلالية',
 'Employer disclosure':'إفصاح من جهة العمل',
 'Secondary evidence':'مصدر ثانوي',
 'Salary estimate':'تقدير راتب',
 'Unverified':'غير متحقق',
 'Source record':'سجل مصدر',
 'Base salary':'الراتب الأساسي',
 'Total compensation / OTE':'التعويض الإجمالي',
 'Advertised pay; base/total not verified':'أجر معلن؛ نوعه غير متحقق',
 'Not disclosed salary':'الراتب غير معلن',
 'Base pay verified':'راتب أساسي متحقق',
 'Verified total pay — separate':'تعويض إجمالي متحقق، منفصل',
 'Pay basis needs review':'نوع الراتب يحتاج مراجعة',
 'Estimate / secondary evidence':'تقدير أو مصدر ثانوي',
 'Excluded from base benchmark':'مستبعد من مقارنة الرواتب الأساسية',
 'Listing verified in feed':'موجود في مصدر التوظيف',
 'Open in feed':'موجود في المصدر',
 'Listing visible':'شوهد سابقًا',
 'Needs recheck':'يحتاج إعادة تحقق',
 'Not in latest feed':'غير موجود في آخر فحص',
 'Archived / unavailable':'مؤرشف أو غير متاح',
 'Historical reference':'مرجع تاريخي',
 'Source check failed':'فشل فحص المصدر',
 'Last seen; recheck due':'آخر ظهور قديم؛ يحتاج فحصًا',
 'Not yet verified open':'لم يتأكد أنه مفتوح',
 'Newly tracked':'رُصد حديثًا',
 'Salary changed':'تغير الراتب',
 'Source status changed':'تغيرت حالة المصدر',
 'Role relevance':'مدى مطابقة التخصص',
 'Pay basis':'نوع الأجر',
 'Saudi listing status':'حالة إعلان سعودي',
 'THE VALUE OF CONNECTED KNOWLEDGE':'قيمة المعرفة المترابطة',
 'Know the market. Know your value.':'اعرف السوق. واعرف قيمة تخصصك.',
 'overviewIntro':'مرجع موثق لرواتب وظائف هندسة المعرفة عالميًا، إلى جانب إعلانات التوظيف المرتبطة بها داخل السعودية.',
 'One reference. Two perspectives.':'مرجع واحد. زاويتان للمقارنة.',
 'Global compensation · Saudi market demand':'الرواتب العالمية · الطلب في السعودية',
 'Verified base-salary references':'مراجع الراتب الأساسي المؤكدة',
 'Not mixed with total pay or estimates':'دون خلطها بالتعويض الإجمالي أو التقديرات',
 'Saudi postings tracked':'إعلانات السعودية المرصودة',
 'Includes unverified and archived records':'تشمل الإعلانات غير المؤكدة والمؤرشفة',
 'Configured public boards':'مصادر التوظيف المهيأة',
 'Coverage limited to these sources':'التغطية مقتصرة على هذه المصادر',
 'Sources checked successfully':'مصادر تم فحصها بنجاح',
 'Successful API checks, not manual review':'فحوص ناجحة للمصادر، لا تعني مراجعة بشرية',
 'Global base salary ranges':'نطاقات الراتب الأساسي العالمية',
 'Gross monthly SAR equivalents · verified employer base pay only':'المقابل الشهري بالريال قبل الاستقطاعات · رواتب أساسية موثقة فقط',
 'Explore':'استكشاف',
 'NEW · SAUDI ARABIA':'الوظائف · السعودية',
 'Where the work is being advertised.':'أين تُعرض وظائف هندسة المعرفة؟',
 'saudiOverviewIntro':'اكتشف فرص الأنطولوجيا والرسوم البيانية المعرفية والدلالات، حتى إن كان المسمى Architect أو Data Engineer.',
 'Explore Saudi opportunities':'استكشاف الفرص السعودية',
 'A FAIR COMPARISON':'مقارنة منصفة',
 'A missing year count does not mean Junior.':'غياب سنوات الخبرة لا يعني أن الوظيفة للمبتدئين.',
 'evidenceOverviewIntro':'تحفظ الخبرة ونوع الأجر وحالة المصدر لكل مرجع. ولا تُستنتج رواتب غير معلنة.',
 'Read the Junior evidence':'عرض أدلة المبتدئين',
 'Review source health before sharing the benchmark.':'راجع حالة المصادر قبل مشاركة الأرقام مع الإدارة.',
 'View update coverage':'عرض تغطية التحديثات',
 'No verified employer base-salary ranges in this selection.':'لا توجد رواتب أساسية موثقة من الجهات في هذا الاختيار.',
 'Research pay ranges · not in headline benchmark':'رواتب للبحث والمراجعة · خارج المقارنة المعتمدة',
 'Salary basis pending verification':'نوع الراتب بانتظار التحقق',
 'These original advertised amounts are presented for research only and are not included in verified base-pay statistics.':'تُعرض هذه المبالغ المعلنة للبحث فقط، ولا تدخل في إحصائيات الراتب الأساسي المعتمد.',
 'chartDisclaimer':'يمثل الرسم نطاقات الرواتب الأساسية المعلنة والمؤكدة فقط، بما فيها مراجع تاريخية. ليس متوسطًا إحصائيًا أو توصية براتب سعودي.',
 'INTERNATIONAL SALARY BENCHMARK':'مرجع الرواتب الدولية',
 'Global salaries.':'الرواتب العالمية.',
 'globalIntro':'قارن الوظائف بحسب الشركة والدولة والخبرة والأجر الشهري، مع إبقاء العملة والمصدر الأصلي متاحين.',
 'Search company, role or skill':'ابحث عن شركة أو وظيفة أو مهارة',
 'Country / market':'الدولة أو السوق',
 'Location':'المدينة',
 'Evidence type':'نوع المصدر',
 'Career level':'المستوى المهني',
 'All':'الكل',
 'All evidence types':'جميع أنواع الأدلة',
 'Employer disclosures':'إفصاحات جهات العمل',
 'Secondary evidence':'مصادر ثانوية',
 'Salary estimates':'تقديرات الرواتب',
 'Exact title: Knowledge Engineer':'المسمى الحرفي: Knowledge Engineer',
 'Disclosed salary only':'الرواتب المعلنة فقط',
 'Include archived postings':'إظهار الإعلانات المؤرشفة',
 'Status':'الحالة',
 'Verified in latest feed':'مؤكد في آخر فحص',
 'Unverified / saved':'محفوظ / يحتاج تحقق',
 'Archived / absent':'مؤرشف أو غير موجود',
 'Reset':'إعادة ضبط',
 'matching references':'مرجع مطابق',
 'Employer base-salary references':'مراجع الراتب الأساسي للجهات',
 'Eligible records in this selection':'مراجع مستوفية لشروط المقارنة',
 'Markets represented':'أسواق ممثلة',
 'Countries in verified-base sample':'الدول ضمن عينة الراتب الأساسي المؤكد',
 'Lowest advertised floor':'أقل حد معلن',
 'Monthly equivalent; not a Junior minimum':'مقابل شهري؛ ليس حدًا أدنى للمبتدئين',
 'Highest advertised ceiling':'أعلى حد معلن',
 'Monthly equivalent; not a typical offer':'مقابل شهري؛ ليس عرضًا نموذجيًا',
 'The salary reference set':'قاعدة المراجع الوظيفية والرواتب',
 'salaryTableIntro':'اختر حتى ثلاث وظائف للمقارنة. لا تُخلط الرواتب غير المؤكدة بالتعويض الإجمالي أو التقديرات.',
 'Export CSV':'تصدير CSV',
 'Role / company':'الوظيفة / الشركة',
 'Market':'السوق',
 'Experience':'الخبرة',
 'Monthly SAR':'شهريًا بالريال',
 'Evidence':'الدليل',
 'Compare':'مقارنة',
 'Source & details':'المصدر والتفاصيل',
 'Review pay basis':'مراجعة نوع الراتب',
 'No matching references':'لا توجد مراجع مطابقة',
 'Change your filters. Missing evidence is not replaced with estimates.':'غيّر خيارات البحث؛ الأدلة المفقودة لا تُستبدل بتقديرات.',
 'LOCAL OPPORTUNITY TRACKER':'متابعة الفرص المحلية',
 'Knowledge Engineering in Saudi Arabia.':'هندسة المعرفة في السعودية.',
 'saudiIntro':'سجل منفصل لوظائف الأنطولوجيا والرسوم البيانية المعرفية والأدوار الدلالية المجاورة. ليست كل المسميات Knowledge Engineer.',
 'saudiSalaryDisclaimer':'هذه الوظائف ليست مرجع رواتب سعوديًا. الرواتب غير المعلنة تبقى فارغة، وحالة الإعلان تعتمد على أحدث تحقق من المصدر.',
 'Postings in this view':'الإعلانات الظاهرة',
 'Saved references, not unique requisitions':'مراجع محفوظة وقد تشمل إعلانات متشابهة',
 'Core KE relevance':'مطابقة أساسية للتخصص',
 'Explicit ontology or knowledge-graph scope':'أنطولوجيا أو Knowledge Graph بمسؤوليات واضحة',
 'Fresh feed-confirmed listings':'وظائف مؤكدة في فحص حديث',
 'Successful, recent public ATS check':'تحقق ناجح وحديث من مصدر التوظيف',
 'Salaries disclosed':'الرواتب المعلنة',
 'No undisclosed Saudi salary is inferred':'لا تُستنتج الرواتب السعودية غير المعلنة',
 'Experience required':'الخبرة المطلوبة',
 'Monthly salary / SAR':'الراتب الشهري / ريال',
 'View original posting':'فتح الإعلان الأصلي',
 'Evidence & notes':'الأدلة والملاحظات',
 'Published':'تاريخ النشر',
 'Last seen in feed':'آخر ظهور في المصدر',
 'Possible overlap; client identity unconfirmed.':'احتمال تكرار الإعلان؛ هوية العميل غير مؤكدة.',
 'No matching Saudi postings':'لا توجد إعلانات سعودية مطابقة',
 'saudiEmpty':'جرّب إظهار الإعلانات المؤرشفة أو تغيير التصنيف. عدم وجود نتيجة لا يعني عدم وجود وظائف في السعودية.',
 'EARLY CAREER / READ CAREFULLY':'المستوى المبكر · قراءة حذرة',
 'Junior evidence, without inflated claims.':'مراجع Junior، دون مبالغة.',
 'juniorIntro':'نعرض فقط الوظائف التي تحمل مستوى Junior أو Entry-Level بوضوح. غياب شرط الخبرة ليس دليلًا على أنها لخريجين جدد.',
 'juniorDisclaimer':'هذه ليست عينة إحصائية موحدة لرواتب المبتدئين. تتضمن المراجع إعلانًا تاريخيًا وتقديرات منصات رواتب، ولا يمكن دمجها في متوسط واحد.',
 'SAR per month, gross equivalent':'ريال شهريًا قبل الاستقطاعات (مكافئ)',
 'Read source evidence':'عرض أدلة المصدر',
 'Compare the scope, then the price':'قارن طبيعة الدور قبل الراتب',
 'juniorMethod':'احتفظ بالدولة والمسؤوليات والخبرة والقيود الخاصة معًا. وقد تؤثر التصاريح الأمنية والقطاع والضرائب والتعويض الإجمالي على المقارنة. الراتب الأمريكي ليس توصية براتب سعودي للمبتدئين.',
 'Browse all salary references':'كل مراجع الرواتب',
 'TRANSPARENCY BY DESIGN':'شفافية موثقة',
 'Sources, freshness and what updates.':'المصادر وحداثة البيانات وآلية التحديث.',
 'sourcesIntro':'تقرأ الصفحة بيانات مشتركة، ويقوم نظام مجدول بجمع إعلانات عامة والتحقق منها ونشر نسخة جديدة. هذه عمليات منفصلة.',
 'Automatic collection':'الجمع التلقائي',
 'Configured':'مهيأ',
 'Not activated':'غير مفعّل',
 'Requires project deployment':'يحتاج نشر المشروع',
 'Browser refresh does not modify collection time':'تحديث المتصفح لا يغير تاريخ جمع المصادر',
 'Public board coverage':'تغطية المصادر العامة',
 'Sources with successful recent checks':'المصادر التي تم فحصها بنجاح',
 'Pending review items':'بنود بانتظار المراجعة',
 'Not part of approved benchmark until reviewed':'لا تدخل المقارنة المعتمدة قبل المراجعة',
 'Scope':'النطاق',
 'Configured public employer/recruiter boards only. Not an exhaustive search of LinkedIn or the entire market.':'مصادر التوظيف العامة المهيأة فقط. لا يشمل فحصًا شاملًا لـLinkedIn أو للسوق بأكمله.',
 'Last attempt':'آخر محاولة',
 'Last successful check':'آخر فحص ناجح',
 'Jobs examined':'وظائف فُحصت',
 'Matched':'مطابقة مبدئية',
 'Open source board':'فتح مصدر الوظائف',
 'How automatic collection works':'كيف تعمل آلية الجمع التلقائي',
 'Collection':'الجمع',
 'Matching':'المطابقة',
 'Salary safeguards':'ضوابط الرواتب',
 'Publication':'النشر',
 'Viewer refresh':'تحديث العرض',
 'sourcesWorkflow':'يفحص النظام مصادر التوظيف العامة يوميًا تقريبًا 08:17 صباحًا بتوقيت الرياض. لا يجمع بيانات LinkedIn مباشرة.',
 'sourcesMatching':'تُقبل المسميات المتخصصة، أما الأدوار غير الواضحة فتُنقل لقائمة المراجعة قبل اعتمادها.',
 'sourcesPay':'لا تُحسب ضمن مرجع الراتب الأساسي إلا إفصاحات صاحب العمل التي توضّح نوع الأجر. تُعرض التعويضات الإجمالية منفصلة.',
 'sourcesPublish':'تنشر GitHub Actions ملف JSON وصفحة HTML تحت نفس الرابط بعد اجتياز الاختبارات.',
 'sourcesViewer':'تفحص الصفحة النسخة المنشورة كل خمس دقائق أثناء فتحها.',
 'sourcesCaveat':'في حال تعذر الوصول لمصدر، نحتفظ بآخر نسخة صالحة. غياب الوظيفة عن فحصين متتاليين لا يثبت إغلاقها. قد يتأخر تنفيذ GitHub Actions.',
 'Open workflow runs':'فتح عمليات GitHub',
 'Exchange rates & salary basis':'أسعار الصرف ونوع الراتب',
 'fxFormula':'المقابل الشهري بالريال = الراتب الأصلي × سعر الصرف؛ ثم القسمة على 12 إذا كان الراتب سنويًا. لا نحول الأجر بالساعة دون افتراض ساعات موثّق.',
 'Rate date':'تاريخ السعر',
 'FX status':'حالة التحويل',
 'Open FX source':'فتح مصدر الصرف',
 'fxCaveat':'الرواتب غير المؤكدة والتقديرات لا تدخل إحصائيات الرواتب الأساسية. لا يتغير تاريخ دليل الراتب الأصلي عند تحديث العملات.',
 'Manage one shared reference':'إدارة مرجع واحد مشترك',
 'manageIntro':'هذه النسخة للقراءة فقط. لإضافة وظيفة موثقة أو تعديلها، عدّل data/curated.json في GitHub. ولإضافة مصدر عدّل config/sources.json. لا تضع أي بيانات شخصية أو رواتب سرية داخل المستودع العام.',
 'Export dataset JSON':'تصدير البيانات JSON',
 'Export all references CSV':'تصدير كل المراجع CSV',
 'saveInfo':'حفظ نسخة ينشئ نسخة HTML غير متصلة، ولا ينشئ موقعًا جديدًا. لا توجد مفاتيح GitHub سرية داخل الصفحة.',
 'Latest recorded changes':'آخر التغييرات المسجلة',
 'No automatic changes recorded.':'لا توجد تغييرات تلقائية مسجلة.',
 'REVIEW BEFORE PUBLICATION':'مراجعة الجودة قبل الاعتماد',
 'Review queue.':'قائمة المراجعة.',
 'reviewIntro':'الإعلانات ذات الصلة غير المؤكدة والرواتب غير الواضحة وحالات الوظائف القديمة تبقى هنا حتى تتوفر أدلة كافية.',
 'Review items':'بنود المراجعة',
 'Role candidates':'مرشحون يحتاجون مراجعة التخصص',
 'Pay basis ambiguities':'رواتب تحتاج توثيق النوع',
 'Saudi status checks':'إعلانات سعودية تحتاج تحقق',
 'Open source':'فتح المصدر',
 'View role':'عرض الوظيفة',
 'No pending review items':'لا توجد بنود مراجعة معلّقة',
 'reviewInstructions':'لا يوجد اعتماد من داخل المتصفح العام. لقبول وظيفة آلية بعد مراجعة مصدرها، أضف معرّفها إلى approved في data/review_decisions.json. للرفض أضفه إلى rejected. راجع نوع الراتب في data/curated.json بعد التوثيق.',
 'Original evidence':'الأدلة الأصلية',
 'MONTHLY EQUIVALENT / SAR':'المقابل الشهري / ريال',
 'No salary conversion is calculated.':'لم يتم احتساب تحويل راتب.',
 'Gross, before tax; not a guaranteed offer.':'قبل الاستقطاعات؛ ليس عرضًا مضمونًا.',
 'Source status':'حالة المصدر',
 'Scope of the role':'نطاق الدور',
 'Evidence & dates':'الأدلة والتواريخ',
 'Evidence date':'تاريخ الدليل',
 'Salary evidence':'دليل الراتب',
 'First tracked automatically':'أول رصد آلي',
 'Limitations & restrictions':'القيود والملاحظات',
 'Curated reference; check original evidence.':'مرجع محفوظ؛ يُرجى التحقق من المصدر الأصلي.',
 'Rule-matched feed role; review the source.':'وظيفة رصدتها قواعد المطابقة؛ راجع وصفها الأصلي.',
 'Client identity unconfirmed.':'هوية العميل غير مؤكدة.',
 'Open source':'فتح المصدر',
 'Close':'إغلاق',
 'Original source':'المصدر الأصلي',
 'ROLE SCOPE':'نطاق العمل',
 'LIMITATIONS':'القيود',
 'EXPERIENCE':'الخبرة',
 'Saved snapshot.':'تم حفظ نسخة.',
 'This offline copy does not activate a live collector.':'النسخة غير المتصلة لا تشغل جمع البيانات.',
 'Already on the latest published snapshot.':'البيانات المنشورة الحالية هي الأحدث.',
 'Published snapshot loaded.':'تم تحميل أحدث بيانات منشورة.',
 'Live refresh unavailable; keeping the previous snapshot.':'تعذر تحديث البيانات؛ تم الاحتفاظ بالنسخة السابقة.',
 'This is an offline preview.':'هذه معاينة دون اتصال.',
 'Select up to three roles.':'يمكن اختيار ثلاث وظائف بحد أقصى.',
 'Source appendix':'ملحق المصادر',
 'No personal data':'لا توجد بيانات شخصية',
 'Review required':'تحتاج مراجعة',
 'Approved / curated':'موثقة أو محفوظة بمراجعة',
 'Not in headline benchmark':'خارج المرجع الرئيسي',
 'Compensation':'التعويض',
 'Role relevance':'مدى مطابقة التخصص',
 'Verified base salary only':'الراتب الأساسي الموثق فقط',
 'Unverified pay visible for research':'الأجور غير المؤكدة ظاهرة للبحث فقط',
 'Saudi posting verification is not salary verification':'التحقق من إعلان سعودي لا يعني التحقق من راتبه',
 'Pending relevance review':'مطابقة التخصص بانتظار المراجعة',
 'Not included in published job totals':'خارج إجمالي الوظائف المنشورة',
 'Source health does not imply all jobs are relevant':'نجاح فحص المصدر لا يعني مطابقة كل إعلاناته',
 'United States':'الولايات المتحدة',
 'United Kingdom':'المملكة المتحدة',
 'Netherlands':'هولندا',
 'Germany':'ألمانيا',
 'Ireland':'أيرلندا',
 'United Arab Emirates':'الإمارات',
 'Europe':'أوروبا',
 'All levels':'جميع المستويات',
 'Multiple levels':'مستويات مختلفة',
 'Needs manual review':'تحتاج مراجعة بشرية',
 'Evidence confirmed for source only':'تم التحقق من المصدر فقط',
};
// Preserve English paragraph copy when a translation uses an internal message key.
const EN={
 overviewIntro:'A traceable salary benchmark for global Knowledge Engineering roles, alongside the opportunities being advertised in Saudi Arabia.',
 saudiOverviewIntro:'Find ontology, knowledge graph and semantic roles — even when the job title says Architect or Data Engineer.',
 evidenceOverviewIntro:'Experience, salary basis and source status are preserved for every reference. No missing salary is converted into an estimate.',
 chartDisclaimer:'The chart shows explicitly verified employer base-salary ranges, including historical references. It is not a market average or a recommended Saudi salary.',
 globalIntro:'Compare source-backed roles by employer, market, experience and monthly salary. Original currencies and evidence remain one click away.',
 salaryTableIntro:'Select up to three roles to compare. Unverified pay, total compensation and estimates stay separate from verified base-salary statistics.',
 saudiIntro:'A separate register of Saudi postings: core semantic roles, applied knowledge graph work, and adjacent metadata positions. Not every title is Knowledge Engineer.',
 saudiSalaryDisclaimer:'Jobs are not Saudi salary benchmarks. Undisclosed salaries stay blank, and listing status depends on the latest source verification.',
 saudiEmpty:'Try including archived records or broader role labels. No result is not proof that no such job exists in Saudi Arabia.',
 juniorIntro:'Only explicitly Junior or entry-level references belong here. A missing experience requirement or an all-level salary range is not evidence of a graduate offer.',
 juniorDisclaimer:'This is not a statistically established Junior salary band. Historical postings and salary-platform estimates are not interchangeable and cannot be combined into one average.',
 juniorMethod:'Keep geography, actual responsibilities, experience and special restrictions together. Defense-related clearance, specialist industries, taxes and total compensation can change the comparison substantially. A US monthly equivalent is not a recommended Saudi starting salary.',
 sourcesIntro:'The browser reads a shared dataset. A scheduled server workflow collects public job boards, validates the result and publishes a new snapshot. These are separate steps.',
 sourcesWorkflow:'The system checks public job boards daily, approximately 08:17 Riyadh time. It does not collect LinkedIn postings directly.',
 sourcesMatching:'Specialist titles are accepted; uncertain related roles enter the review queue before approval.',
 sourcesPay:'Only employer disclosures explicitly identifying the pay basis enter the base-salary benchmark. Total compensation is shown separately.',
 sourcesPublish:'GitHub Actions publishes the updated JSON and HTML to the same site URL after checks pass.',
 sourcesViewer:'The open dashboard checks for a new published snapshot every five minutes.',
 sourcesCaveat:'API failures preserve last-good records. A role missing from two complete checks is marked absent from the feed, not definitively closed. GitHub schedules can be delayed.',
 fxFormula:'Monthly SAR = original salary × FX rate, divided by 12 for annual salaries. Hourly pay is not annualized without explicit working-time assumptions.',
 fxCaveat:'Unverified pay and estimates do not enter base-salary statistics. Original salary evidence dates do not change when exchange rates refresh.',
 manageIntro:'This online edition is read-only for visitors. The repository is the central source of truth. To add or correct an approved reference, edit data/curated.json and publish; to add a feed, edit config/sources.json. Do not put private notes, contacts or confidential salary information in a public repository.',
 saveInfo:'Save copy produces an offline snapshot, not another live deployment. No editing keys or GitHub tokens are placed in this page.',
 reviewIntro:'Uncertain role matches, unclear salary evidence and older listing statuses remain here until sufficient evidence is available.',
 reviewInstructions:'The public dashboard does not approve records. After reviewing an automatic candidate\'s source, add its ID to approved or rejected in data/review_decisions.json. Verify salary basis separately in data/curated.json before updating the evidence.',
};
const t=key=>lang==='ar'?(AR[key]||key):(EN[key]||key);
const h=key=>esc(t(key));
const num=n=>n==null?t('Not disclosed'):new Intl.NumberFormat('en-US',{maximumFractionDigits:0}).format(n);
const locale=()=>lang==='ar'?'ar-SA':'en-GB';
function dte(value,withTime=false){
 if(!value)return t(withTime?'Never':'Not recorded');
 const d=new Date(value.length===10?value+'T12:00:00Z':value);
 if(Number.isNaN(d.getTime()))return t('Not recorded');
 const options={day:'2-digit',month:'short',year:'numeric',timeZone:'Asia/Riyadh'};
 if(withTime){options.hour='2-digit';options.minute='2-digit';}
 return new Intl.DateTimeFormat(locale(),options).format(d)+(withTime?' AST':'');
}
const hoursAgo=value=>value?Math.max(0,(Date.now()-Date.parse(value))/3600000):Infinity;
const seed=JSON.parse($('#seed-data').textContent);
let market=clone(seed),view='overview',networkMode='initial',busy=false,toastTimer;
let selected=new Set();
const defaults={q:'',country:'all',city:'all',level:'all',evidence:'all',relevance:'all',status:'all',exact:false,archive:false,onlySalary:true};
const filters={global:{...defaults},saudi:{...defaults},review:{...defaults}};
function validate(dataset){
 if(!dataset||dataset.schemaVersion!==2||!Array.isArray(dataset.records)||dataset.records.length>10000||!Array.isArray(dataset.sources)||!dataset.meta||!dataset.fx?.rates)throw Error('Unsupported dataset');
 const ids=new Set();for(const r of dataset.records){
  if(!r||typeof r.id!=='string'||ids.has(r.id)||typeof r.company!=='string'||typeof r.title!=='string'||!Array.isArray(r.skills)||validUrl(r.sourceUrl)==='#')throw Error('Invalid record');
  ids.add(r.id);
  if(r.salaryMin!=null&&(!Number.isFinite(r.salaryMin)||r.salaryMin<0||!['Annual','Monthly'].includes(r.period)||!Number.isFinite(dataset.fx.rates[r.currency])))throw Error('Invalid salary');
  if(r.salaryMax!=null&&(!Number.isFinite(r.salaryMax)||r.salaryMax<r.salaryMin))throw Error('Invalid range');
  if(r.salaryEligible&&!(r.salaryBasis==='base'&&r.salaryBasisVerified&&r.evidenceType==='employer'))throw Error('Unverified base salary flagged eligible');
 }
 if(dataset.fx.rates.SAR!==1||Object.values(dataset.fx.rates).some(x=>!Number.isFinite(x)||x<=0))throw Error('Invalid FX');
 if(!Array.isArray(dataset.reviewQueue))dataset.reviewQueue=[];
 return dataset;
}
try{if(location.protocol!=='file:'){const cached=localStorage.getItem(CACHE);if(cached){const candidate=validate(JSON.parse(cached));if(String(candidate.meta.lastAttemptAt||'')>String(market.meta.lastAttemptAt||'')){market=candidate;networkMode='cached';}}}}catch{}
function toast(text){$('#toast').textContent=text;$('#toast').hidden=false;clearTimeout(toastTimer);toastTimer=setTimeout(()=>$('#toast').hidden=true,4800);}
function isSalary(r){return r.salaryMin!=null&&Number.isFinite(market.fx.rates[r.currency])&&['Annual','Monthly'].includes(r.period);}
const baseEligible=r=>r.region!=='saudi'&&r.roleDecision!=='pending'&&r.evidenceType==='employer'&&r.salaryEligible===true&&r.salaryBasis==='base'&&r.salaryBasisVerified===true&&isSalary(r);
const totalEligible=r=>r.evidenceType==='employer'&&r.salaryBasis==='total'&&r.salaryBasisVerified===true&&isSalary(r);
function monthly(r,key='salaryMin'){return isSalary(r)&&r[key]!=null?r[key]*market.fx.rates[r.currency]/(r.period==='Annual'?12:1):null;}
function payRange(r){if(!isSalary(r))return t('Not disclosed');const lo=monthly(r),hi=monthly(r,'salaryMax');return hi==null?t('From')+' '+num(lo):lo===hi?num(lo):num(lo)+'–'+num(hi);}
function originalPay(r){if(!isSalary(r))return t('Not disclosed');let s=r.currency+' '+num(r.salaryMin);if(r.salaryMax!=null&&r.salaryMax!==r.salaryMin)s+='–'+num(r.salaryMax);return s+' / '+t(r.period==='Annual'?'year':'month');}
function expText(r){const v=r.experience||'Not specified';if(lang!=='ar')return v;if(['Not specified','Not reverified'].includes(v))return t('Not specified');const range=/^(\d+)(?:-(\d+))?\+?\s*years?\b/i.exec(v);if(range)return range[1]+(range[2]?'–'+range[2]:'+')+' '+t('years');if(/less than 1 year/i.test(v))return 'أقل من سنة';return v;}
function reLabel(r){return t(r.relevance||'Not specified');}
function recordSummary(r){return lang==='ar'?(r.summaryAr|| (r.collection==='automatic'?'مهارات وردت في وصف الوظيفة: '+(r.skills||[]).join('، ')+'. تحقق من المسؤوليات في المصدر الأصلي.':r.summary)):r.summary;}
const badge=(text,color='')=>`<span class="chip ${color}">${esc(text)}</span>`;
function relevanceBadge(r){return badge(reLabel(r),r.relevance==='Core KE'?'green':r.relevance==='Applied KG / AI'?'blue':'');}
function evidenceBadge(r){const key=({employer:'Employer disclosure',reposted:'Secondary evidence',estimate:'Salary estimate',user:'Unverified'})[r.evidenceType]||'Source record';return badge(t(key),r.evidenceType==='employer'?'green':r.evidenceType==='estimate'?'blue':'amber');}
function basisBadge(r){if(!isSalary(r))return badge(t('Not disclosed'));
 if(baseEligible(r))return badge(t('Base pay verified'),'green');
 if(totalEligible(r))return badge(t('Verified total pay — separate'),'blue');
 if(r.evidenceType==='reposted'||r.evidenceType==='estimate')return badge(t('Estimate / secondary evidence'),'amber');
 return badge(t('Pay basis needs review'),'amber');}
const isArchived=r=>['Archived / unavailable','Not in latest feed'].includes(r.listingStatus);
function feedVerified(r){const s=market.sources.find(x=>x.id===r.sourceId);return r.region==='saudi'&&r.listingStatus==='Open in feed'&&!!s&&s.status.startsWith('OK')&&hoursAgo(r.lastSeenAt)<=market.meta.staleAfterHours;}
function statusBadge(r){if(feedVerified(r))return badge(t('Listing verified in feed'),'green');
 if(r.listingStatus==='Archived / unavailable'||r.listingStatus==='Not in latest feed')return badge(t(r.listingStatus),'red');
 if(r.listingStatus==='Open in feed')return badge(t('Last seen; recheck due'),'amber');
 if(r.listingStatus==='Historical reference')return badge(t('Historical reference'));
 return badge(t('Not yet verified open'),'amber');}
const newTrack=r=>r.collection==='automatic'&&r.firstSeenAt&&hoursAgo(r.firstSeenAt)<168;
const initials=name=>name.split(/\s+/).filter(Boolean).map(s=>s[0]).slice(0,2).join('').toUpperCase();
function st(label,value,foot,featured=false){return `<article class="stat${featured?' emph':''}"><div class="label">${h(label)}</div><div class="value mono">${value}</div><div class="foot">${h(foot)}</div></article>`;}
function head(kicker,title,description,note=''){return `<div class="page-heading"><div><span class="eyebrow">${h(kicker)}</span><h1>${title}</h1><p>${esc(description)}</p></div>${note?`<div class="heading-note">${note}</div>`:''}</div>`;}
function applyLanguage(){
 document.documentElement.lang=lang;
 document.documentElement.dir=lang==='ar'?'rtl':'ltr';
 document.title=lang==='ar'?'هندسة المعرفة | مرصد السوق':'Knowledge Engineering | Market Observatory';
 $$('[data-i18n]').forEach(node=>{
  const key=node.dataset.i18n;
  node.textContent=t(key);
 });
 $('#lang-switch').textContent=lang==='ar'?'English':'العربية';
 $('#lang-switch').lang=lang==='ar'?'en':'ar';
 $('#lang-switch').setAttribute('aria-label',lang==='ar'?'Switch to English':'التبديل إلى العربية');
}
function renderShell(){
 applyLanguage();
 $('#global-count').textContent=num(market.records.filter(r=>r.region!=='saudi'&&isSalary(r)).length);
 $('#saudi-count').textContent=num(market.records.filter(r=>r.region==='saudi').length);
 $('#review-count').textContent=num(market.reviewQueue.length);
 const meta=market.meta,last=meta.lastSuccessfulCollectionAt;
 const ready=meta.automationActivated&&last&&hoursAgo(last)<=meta.staleAfterHours;
 const local=!['http:','https:'].includes(location.protocol);
 let pill='Prepared for deployment',notice='Daily collection has not been activated.';
 if(local){pill='Offline preview';notice='This preview is not a live site. Data collection activates after deployment.';}
 else if(networkMode==='failed'){pill='Update unavailable';notice='Showing the embedded or last saved snapshot because the update failed.';}
 else if(ready){pill='Snapshot connected';notice=t('Last successful collection')+': '+dte(last,true)+'. '+t('The browser checks published data every 5 minutes; the scheduled workflow checks sources daily.');}
 else if(meta.automationActivated){pill='Check collection health';notice='The last successful collection is missing or stale. Verify the source status.';}
 $('#sync-pill').textContent=t(pill);
 $('#sync-pill').classList.toggle('ok',!!ready&&!local&&networkMode!=='failed');
 $('#connection-notice').textContent=t(notice);
 $('#connection-notice').classList.toggle('ok',!!ready&&!local&&networkMode!=='failed');
 $('#side-mode').textContent=t(ready?'Daily collection configured':'Prepared for deployment');
 $('#footer-evidence').textContent='FX '+dte(market.fx.date)+' · '+t('Source-level evidence dates retained');
 $$('nav [data-view]').forEach(b=>{
  b.classList.toggle('active',b.dataset.view===view);
  if(b.dataset.view===view)b.setAttribute('aria-current','page');else b.removeAttribute('aria-current');
 });
 $('#crumb-title').textContent=t(({overview:'OVERVIEW',global:'GLOBAL SALARIES',saudi:'SAUDI ARABIA',junior:'JUNIOR EVIDENCE',sources:'SOURCES & UPDATES',review:'REVIEW QUEUE'})[view]);
 renderTray();
}
function graph(rows){
 const sample=rows.filter(baseEligible).sort((a,b)=>monthly(a)-monthly(b));
 if(!sample.length)return `<div class="empty">${h('No verified employer base-salary ranges in this selection.')}</div>`;
 const ceiling=Math.max(10000,Math.ceil(Math.max(...sample.map(r=>monthly(r,'salaryMax')??monthly(r)))/10000)*10000);
 return `<div class="chart"><div class="chart-legend"><span>0</span><span>${num(ceiling/2)}</span><span>${num(ceiling)} SAR</span></div>${sample.map(r=>{
  const min=monthly(r),max=monthly(r,'salaryMax')??min;
  return `<div class="chart-row"><button class="text-button chart-role" data-detail="${esc(r.id)}">${esc(r.company)}<small>${esc(r.title)}</small></button><div class="bar-track" role="img" aria-label="${esc(r.company+' · '+payRange(r)+' SAR')}"><span class="bar-range" style="left:${Math.max(0,min/ceiling*100)}%;width:${Math.max(.6,(max-min)/ceiling*100)}%"></span></div><div class="chart-value mono">${esc(payRange(r))}</div></div>`;
 }).join('')}<div class="caption">${h('chartDisclaimer')}</div></div>`;
}
function researchRanges(){
 const rows=market.records.filter(r=>r.region!=='saudi'&&isSalary(r)&&r.evidenceType==='employer'&&!baseEligible(r)).slice(0,5);
 if(!rows.length)return '';
 return `<section class="research-ranges"><h3>${h('Research pay ranges · not in headline benchmark')}</h3><p>${h('These original advertised amounts are presented for research only and are not included in verified base-pay statistics.')}</p>`
 +rows.map(r=>`<div class="research-row"><button class="text-button" data-detail="${esc(r.id)}">${esc(r.company)}<small>${esc(r.title)}</small></button><strong dir="auto">${esc(payRange(r))}</strong></div>`).join('')
 +`<span class="chip amber">${h('Salary basis pending verification')}</span></section>`;
}
function overview(){
 const salaryRows=market.records.filter(baseEligible),saudiRows=market.records.filter(r=>r.region==='saudi');
 const ok=market.sources.filter(s=>s.status.startsWith('OK')).length;
 const note=`<strong>${h('One reference. Two perspectives.')}</strong>${h('Global compensation · Saudi market demand')}`;
 $('#view-content').innerHTML=head('THE VALUE OF CONNECTED KNOWLEDGE',h('Know the market. Know your value.'),t('overviewIntro'),note)
 +`<div class="stats">${st('Verified base-salary references',num(salaryRows.length),'Not mixed with total pay or estimates')}${st('Saudi postings tracked',num(saudiRows.length),'Includes unverified and archived records')}${st('Configured public boards',num(market.sources.length),'Coverage limited to these sources')}${st('Sources checked successfully',num(ok)+'<small> / '+num(market.sources.length)+'</small>','Successful API checks, not manual review',true)}</div>`
 +`<div class="overview-grid"><section class="panel"><div class="panel-header"><div><h2>${h('Global base salary ranges')}</h2><p>${h('Gross monthly SAR equivalents · verified employer base pay only')}</p></div><button class="text-button" data-view="global">${h('Explore')} →</button></div>${graph(salaryRows)}${researchRanges()}</section>`
 +`<aside class="overview-aside"><section class="hero-card"><span class="eyebrow">${h('NEW · SAUDI ARABIA')}</span><h2>${h('Where the work is being advertised.')}</h2><p>${h('saudiOverviewIntro')}</p><button class="button" data-view="saudi">${h('Explore Saudi opportunities')} →</button></section>`
 +`<section class="panel evidence-card"><span class="eyebrow muted">${h('A FAIR COMPARISON')}</span><h3 style="margin-top:15px">${h('A missing year count does not mean Junior.')}</h3><p>${h('evidenceOverviewIntro')}</p><div class="thin-rule"></div><button class="text-button" data-view="junior">${h('Read the Junior evidence')} →</button><p style="margin:15px 0 0">${h('Review source health before sharing the benchmark.')}</p><button class="text-button" data-view="review">${h('Review queue')} →</button><p style="margin-top:12px"><button class="text-button" data-view="sources">${h('View update coverage')} →</button></p></section></aside></div>`;
}
function optionList(items,current){return `<option value="all">${h('All')}</option>`+[...new Set(items)].filter(Boolean).sort().map(x=>`<option value="${esc(x)}"${x===current?' selected':''}>${esc(t(x))}</option>`).join('');}
function filterMarkup(scope){
 const f=filters[scope],records=market.records.filter(r=>scope==='saudi'?r.region==='saudi':r.region!=='saudi');
 const search=`<div class="field"><label for="filter-search">${h('Search company, role or skill')}</label><input id="filter-search" data-filter="q" type="search" value="${esc(f.q)}" placeholder="Ontology, Neo4j, company..."></div>`;
 const marketFilter=scope==='saudi'?`<div class="field"><label for="filter-city">${h('Location')}</label><select id="filter-city" data-filter="city">${optionList(records.map(r=>r.city),f.city)}</select></div><div class="field"><label for="filter-rel">${h('Role relevance')}</label><select id="filter-rel" data-filter="relevance">${optionList(records.map(r=>r.relevance),f.relevance)}</select></div>`
 :`<div class="field"><label for="filter-country">${h('Country / market')}</label><select id="filter-country" data-filter="country">${optionList(records.map(r=>r.country),f.country)}</select></div><div class="field"><label for="filter-evidence">${h('Evidence type')}</label><select id="filter-evidence" data-filter="evidence"><option value="all">${h('All evidence types')}</option><option value="employer" ${f.evidence==='employer'?'selected':''}>${h('Employer disclosures')}</option><option value="reposted" ${f.evidence==='reposted'?'selected':''}>${h('Secondary evidence')}</option><option value="estimate" ${f.evidence==='estimate'?'selected':''}>${h('Salary estimates')}</option></select></div>`;
 const statusFilter=scope==='saudi'?`<div class="field"><label for="filter-status">${h('Status')}</label><select id="filter-status" data-filter="status"><option value="all">${h('All')}</option><option value="verified" ${f.status==='verified'?'selected':''}>${h('Verified in latest feed')}</option><option value="unverified" ${f.status==='unverified'?'selected':''}>${h('Unverified / saved')}</option><option value="archived" ${f.status==='archived'?'selected':''}>${h('Archived / absent')}</option></select></div>`:'';
 const levelFilter=`<div class="field"><label for="filter-level">${h('Career level')}</label><select id="filter-level" data-filter="level">${optionList(records.map(r=>r.level),f.level)}</select></div>`;
 return `<section class="filters" aria-label="Filters"><div class="filter-grid">${search}${marketFilter}${levelFilter}${statusFilter}</div><div class="filter-bottom"><div><label class="check-label"><input type="checkbox" data-filter="exact"${f.exact?' checked':''}>${h('Exact title: Knowledge Engineer')}</label>${scope==='saudi'?`<label class="check-label"><input type="checkbox" data-filter="archive"${f.archive?' checked':''}>${h('Include archived postings')}</label>`:`<label class="check-label"><input type="checkbox" data-filter="onlySalary"${f.onlySalary?' checked':''}>${h('Disclosed salary only')}</label>`}<button class="text-button" data-reset="${scope}">${h('Reset')}</button></div><span class="result-count" id="result-count"></span></div></section>`;
}
function filtered(scope){
 const f=filters[scope];
 return market.records.filter(r=>{
  if(scope==='saudi'?r.region!=='saudi':r.region==='saudi')return false;
  if(scope==='saudi'&&!f.archive&&f.status!=='archived'&&isArchived(r))return false;
  if(scope!=='saudi'&&f.onlySalary&&!isSalary(r))return false;
  if(scope==='saudi'&&f.status==='verified'&&!feedVerified(r))return false;
  if(scope==='saudi'&&f.status==='unverified'&&(feedVerified(r)||isArchived(r)))return false;
  if(scope==='saudi'&&f.status==='archived'&&!isArchived(r))return false;
  const hay=[r.company,r.title,r.country,r.city,r.summary,r.summaryAr,...r.skills].join(' ').toLowerCase();
  return (!f.q||hay.includes(f.q.trim().toLowerCase()))
   &&(f.country==='all'||r.country===f.country)&&(f.city==='all'||r.city===f.city)
   &&(f.level==='all'||r.level===f.level)&&(f.relevance==='all'||r.relevance===f.relevance)
   &&(f.evidence==='all'||r.evidenceType===f.evidence)
   &&(!f.exact||r.title.trim().toLowerCase()==='knowledge engineer');
 }).sort((a,b)=>scope==='saudi'?({'Core KE':0,'Applied KG / AI':1,'Metadata / Semantic':2}[a.relevance]??3)-({'Core KE':0,'Applied KG / AI':1,'Metadata / Semantic':2}[b.relevance]??3)||(feedVerified(b)?1:0)-(feedVerified(a)?1:0)||a.company.localeCompare(b.company):(monthly(a)??Infinity)-(monthly(b)??Infinity));
}
function salaryStats(rows){
 const base=rows.filter(baseEligible),mins=base.map(r=>monthly(r)),maxes=base.map(r=>monthly(r,'salaryMax')).filter(x=>x!=null);
 return `<div class="stats">${st('Employer base-salary references',num(base.length),'Eligible records in this selection')}${st('Markets represented',num(new Set(base.map(r=>r.country)).size),'Countries in verified-base sample')}${st('Lowest advertised floor',mins.length?'<small>SAR</small>'+num(Math.min(...mins)):'—','Monthly equivalent; not a Junior minimum')}${st('Highest advertised ceiling',maxes.length?'<small>SAR</small>'+num(Math.max(...maxes)):'—','Monthly equivalent; not a typical offer',true)}</div>`;
}
function salaryTable(rows){
 return `<section class="panel"><div class="panel-header"><div><h2>${h('The salary reference set')}</h2><p>${h('salaryTableIntro')}</p></div><button class="button small" data-export="csv">${h('Export CSV')} ↓</button></div><div class="table-scroll"><table><thead><tr><th style="width:28%">${h('Role / company')}</th><th style="width:14%">${h('Market')}</th><th style="width:17%">${h('Experience')}</th><th style="width:22%">${h('Monthly SAR')}</th><th style="width:19%">${h('Evidence')}</th></tr></thead><tbody>`+rows.map(r=>`<tr><td><button class="title-link" data-detail="${esc(r.id)}">${esc(r.title)}</button><span class="subline">${esc(r.company)}</span><span class="subline"><label class="check-label"><input type="checkbox" data-compare="${esc(r.id)}" ${selected.has(r.id)?'checked':''}>${h('Compare')}</label></span></td><td>${esc(t(r.country))}<span class="subline">${esc(r.city)}</span></td><td>${esc(expText(r))}<span class="subline">${esc(t(r.level))}</span></td><td><div class="money mono" dir="auto">${esc(payRange(r))}<small>${esc(originalPay(r))}</small></div>${basisBadge(r)}${!baseEligible(r)?`<small class="pay-note">${h('Excluded from base benchmark')}</small>`:''}</td><td>${evidenceBadge(r)}<span class="subline">${h('Evidence date')}: ${dte(r.salaryVerifiedAt||r.evidenceDate)}</span><button class="text-button" data-detail="${esc(r.id)}" style="font-size:10px;margin-top:8px">${h('Source & details')} ↗</button></td></tr>`).join('')+`</tbody></table></div>${!rows.length?`<div class="empty"><strong>${h('No matching references')}</strong>${h('Change your filters. Missing evidence is not replaced with estimates.')}</div>`:''}</section>`;
}
function globalPage(){
 $('#view-content').innerHTML=head('INTERNATIONAL SALARY BENCHMARK',h('Global salaries.'),t('globalIntro'))
 +`<div class="notice">${h('Verified base salary only')} · ${h('Unverified pay visible for research')}</div>`
 +filterMarkup('global')+'<div id="results"></div>';
 renderResults();
}
function saudiPage(){
 $('#view-content').innerHTML=head('LOCAL OPPORTUNITY TRACKER',h('Knowledge Engineering in Saudi Arabia.'),t('saudiIntro'))
 +`<div class="notice">${h('saudiSalaryDisclaimer')}</div>`
 +filterMarkup('saudi')+'<div id="results"></div>';
 renderResults();
}
function saudiCards(rows){return `<div class="cards-grid">`+rows.map(r=>`<article class="job-card"><div class="job-brand"><span class="company-mark">${esc(initials(r.company))}</span><span>${esc(r.company)}</span>${newTrack(r)?badge(t('Newly tracked'),'green'):''}</div><h3><button class="title-link" style="font-size:inherit" data-detail="${esc(r.id)}">${esc(r.title)}</button></h3><div class="job-location">${esc(r.city)} · ${h('Saudi Arabia')}</div><div class="chip-row">${relevanceBadge(r)}${statusBadge(r)}</div><p class="job-summary">${esc(recordSummary(r))}</p><div class="chip-row" style="margin-bottom:14px">${r.skills.slice(0,4).map(s=>badge(s)).join('')}</div><div class="job-facts"><div><small>${h('Experience required')}</small><strong>${esc(expText(r))}</strong></div><div><small>${h('Monthly salary / SAR')}</small><strong>${esc(payRange(r))}</strong></div></div><div class="job-footer">${link(r.sourceUrl,t('View original posting'),'button small')}<button class="text-button" data-detail="${esc(r.id)}">${h('Evidence & notes')} →</button></div><div class="job-dates">${h('Published')}: ${dte(r.postedAt)} · ${h('Evidence date')}: ${dte(r.evidenceDate)}${r.lastSeenAt?'<br>'+h('Last seen in feed')+': '+dte(r.lastSeenAt,true):''}${r.duplicateGroup?'<br>'+h('Possible overlap; client identity unconfirmed.'):''}</div></article>`).join('')+`</div>${!rows.length?`<div class="panel empty"><strong>${h('No matching Saudi postings')}</strong>${h('saudiEmpty')}</div>`:''}`;}
function renderResults(){
 const rows=filtered(view);
 $('#result-count').textContent=num(rows.length)+' '+t('matching references');
 if(view==='global'){$('#results').innerHTML=salaryStats(rows)+salaryTable(rows);return;}
 const verified=rows.filter(feedVerified),core=rows.filter(r=>r.relevance==='Core KE');
 $('#results').innerHTML=`<div class="stats">${st('Postings in this view',num(rows.length),'Saved references, not unique requisitions')}${st('Core KE relevance',num(core.length),'Explicit ontology or knowledge-graph scope')}${st('Fresh feed-confirmed listings',num(verified.length),'Successful, recent public ATS check')}${st('Salaries disclosed',num(rows.filter(isSalary).length),'No undisclosed Saudi salary is inferred',true)}</div>`
 +`<div class="status-legend">${badge(t('Listing verified in feed'),'green')}${badge(t('Not yet verified open'),'amber')}${badge(t('Archived / unavailable'),'red')}<span>${h('Saudi posting verification is not salary verification')}</span></div>`+saudiCards(rows);
}
function juniorPage(){
 const rows=market.records.filter(r=>r.region!=='saudi'&&r.level==='Junior'&&isSalary(r));
 $('#view-content').innerHTML=head('EARLY CAREER / READ CAREFULLY',h('Junior evidence, without inflated claims.'),t('juniorIntro'))
 +`<div class="notice amber"><strong>${h('juniorDisclaimer')}</strong></div><div class="junior-grid">`
 +rows.map(r=>`<article class="panel junior-card">${evidenceBadge(r)}<h3>${esc(r.title)}</h3><small>${esc(r.company==='Market estimate'?r.sourceLabel:r.company)} · ${esc(t(r.country))}</small><div class="junior-money mono">${esc(payRange(r))}</div><small>${h('SAR per month, gross equivalent')}</small><p style="margin-top:17px">${esc(expText(r))}<br>${esc(t(r.compensation))}</p><p>${esc(lang==='ar'&&r.summaryAr?r.summaryAr:r.notes)}</p><button class="button small" data-detail="${esc(r.id)}">${h('Read source evidence')} ↗</button></article>`).join('')
 +`</div><section class="panel method-card" style="margin-top:22px"><h2>${h('Compare the scope, then the price')}</h2><p>${h('juniorMethod')}</p><button class="text-button" data-view="global">${h('Browse all salary references')} →</button></section>`;
}
function sourceHealthCard(s){
 return `<section class="panel source-card"><div class="source-top"><div><h3>${esc(s.company)}</h3><small>${esc(s.type.toUpperCase())} · ${esc(s.account)}</small></div>${badge(s.status,s.status.startsWith('OK')?'green':s.status==='Check failed'?'amber':'')}</div><p>${esc(s.scope)}</p><div class="source-facts">${h('Last attempt')}: ${dte(s.lastAttemptAt,true)}<br>${h('Last successful check')}: ${dte(s.lastSuccessAt,true)}<br>${h('Jobs examined')}: ${s.jobCount==null?t('Not specified'):num(s.jobCount)} · ${h('Matched')}: ${s.matchedCount==null?t('Not specified'):num(s.matchedCount)}</div>${s.error?`<p class="source-error">${esc(s.error)}</p>`:''}${link(s.boardUrl,t('Open source board'),'text-button')}</section>`;
}
function sourcesPage(){
 const meta=market.meta,healthy=market.sources.filter(s=>s.status.startsWith('OK')).length;
 const FX=market.fx;
 $('#view-content').innerHTML=head('TRANSPARENCY BY DESIGN',h('Sources, freshness and what updates.'),t('sourcesIntro'))
 +`<div class="stats">${st('Automatic collection',h(meta.automationActivated?'Configured':'Not activated'),'Requires project deployment')}${st('Last successful collection',dte(meta.lastSuccessfulCollectionAt),'Browser refresh does not modify collection time')}${st('Public board coverage',num(healthy)+'<small> / '+num(market.sources.length)+'</small>','Sources with successful recent checks')}${st('Pending review items',num(market.reviewQueue.length),'Not part of approved benchmark until reviewed',true)}</div>`
 +`<div class="notice"><strong>${h('Scope')}:</strong> ${h(meta.coverage||'Configured public employer/recruiter boards only. Not an exhaustive search of LinkedIn or the entire market.')} <span>${h('Source health does not imply all jobs are relevant')}</span></div>`
 +`<div class="source-grid">${market.sources.map(sourceHealthCard).join('')}</div>`
 +`<div class="method-grid"><section class="panel method-card"><h2>${h('How automatic collection works')}</h2><ol><li>${h('sourcesWorkflow')}</li><li>${h('sourcesMatching')}</li><li>${h('sourcesPay')}</li><li>${h('sourcesPublish')}</li><li>${h('sourcesViewer')}</li></ol><p>${h('sourcesCaveat')}</p>${meta.repositoryUrl?link(meta.repositoryUrl+'/actions',t('Open workflow runs'),'button small'):''}</section>`
 +`<section class="panel method-card"><h2>${h('Exchange rates & salary basis')}</h2><p>${h('fxFormula')}</p><div class="code" dir="ltr">USD → SAR ${esc(String(FX.rates.USD))}<br>GBP → SAR ${esc(String(FX.rates.GBP))}<br>EUR → SAR ${esc(String(FX.rates.EUR))}</div><p>${h('Rate date')}: ${dte(FX.date)}<br>${h('FX status')}: ${esc(FX.status)}<br>${esc(FX.label)}</p><p>${esc(FX.usdSarBasis)}</p>${link(FX.source,t('Open FX source'),'text-button')}<p style="margin-top:14px">${h('fxCaveat')}</p></section>`
 +`<section class="panel method-card"><h2>${h('Manage one shared reference')}</h2><p>${h('manageIntro')}</p><div class="actions"><button class="button small" data-export="json">${h('Export dataset JSON')}</button><button class="button small" id="export-all-csv">${h('Export all references CSV')}</button></div><p style="margin-top:14px">${h('saveInfo')}</p></section>`
 +`<section class="panel method-card"><h2>${h('Review queue')}</h2><p>${h('reviewIntro')}</p><button class="button small" data-view="review">${h('Review queue')} (${num(market.reviewQueue.length)}) →</button><p style="margin-top:15px">${h('reviewInstructions')}</p></section></div>`
 +`<section class="panel method-card"><h2>${h('Latest recorded changes')}</h2>${market.changes.length?market.changes.slice(0,15).map(c=>`<div class="update-event">${badge(t(c.type),c.type==='Newly tracked'?'green':'')} <strong>${esc(c.company)} · ${esc(c.title)}</strong><small>${dte(c.at,true)}</small></div>`).join(''):`<p>${h('No automatic changes recorded.')}</p>`}</section>`;
}
function reviewExplanation(item){
 if(lang!=='ar')return item.reason;
 if(item.category==='Pay basis')return 'النطاق المالي معلن، لكن لا يوجد دليل كافٍ يثبت هل هو الراتب الأساسي أم التعويض الإجمالي؛ لذلك هو خارج الإحصائيات المعتمدة.';
 if(item.category==='Saudi listing status')return 'ظهر الإعلان في مصدر سابق، لكن لم يتم التحقق من بقاء التقديم مفتوحًا عبر فحص حديث وناجح.';
 return 'الوصف يتضمن مصطلحات من هندسة المعرفة لكن مسؤولياته أو مسماه لا تتطابق بوضوح؛ يتطلب مراجعة يدوية قبل اعتماده.';
}
function reviewPage(){
 const items=market.reviewQueue||[];
 const counts={'Role relevance':0,'Pay basis':0,'Saudi listing status':0};
 for(const x of items)counts[x.category]=(counts[x.category]||0)+1;
 $('#view-content').innerHTML=head('REVIEW BEFORE PUBLICATION',h('Review queue.'),t('reviewIntro'))
 +`<div class="stats">${st('Review items',num(items.length),'Not part of approved benchmark until reviewed')}${st('Role candidates',num(counts['Role relevance']||0),'Not included in published job totals')}${st('Pay basis ambiguities',num(counts['Pay basis']||0),'Not in headline benchmark')}${st('Saudi status checks',num(counts['Saudi listing status']||0),'Needs manual review',true)}</div>`
 +`<div class="review-note">${h('reviewInstructions')}</div><div class="review-list">`
 +items.map(item=>`<article class="review-card"><div>${badge(t(item.category),'amber')}<h3>${esc(item.title)}</h3><small>${esc(item.company)} · <code>${esc(item.id)}</code></small><p>${esc(reviewExplanation(item))}</p></div><div class="review-actions">${link(item.sourceUrl,t('Open source'),'button small')}${market.records.find(r=>r.id===item.id)?`<button class="text-button" data-detail="${esc(item.id)}">${h('View role')} →</button>`:''}</div></article>`).join('')
 +`${!items.length?`<div class="panel empty"><strong>${h('No pending review items')}</strong></div>`:''}</div>`;
}
function mount(page){
 if(!['overview','global','saudi','junior','sources','review'].includes(page))page='overview';
 view=page;renderShell();({overview,global:globalPage,saudi:saudiPage,junior:juniorPage,sources:sourcesPage,review:reviewPage})[view]();
 if(location.hash!=='#'+page)try{history.replaceState(null,'','#'+page);}catch{}
}
function details(id){
 const r=market.records.find(record=>record.id===id);
 if(!r)return;
 const conversion=isSalary(r)?`${num(r.salaryMin)}${r.period==='Annual'?' / 12':''} × ${market.fx.rates[r.currency]} = ${num(monthly(r))} SAR/${t('month')}`:t('No salary conversion is calculated.');
 const recordNote=r.collection==='automatic'?t('Rule-matched feed role; review the source.'):t('Curated reference; check original evidence.');
 $('#detail-body').innerHTML=`<h2 class="detail-title" id="detail-heading">${esc(r.title)}</h2><p class="muted">${esc(r.company)} · ${esc(r.city)}, ${esc(t(r.country))}</p><div class="chip-row">${relevanceBadge(r)}${evidenceBadge(r)}${r.region==='saudi'?statusBadge(r):basisBadge(r)}</div>`
 +`<section class="detail-salary"><small>${h('MONTHLY EQUIVALENT / SAR')}</small><div class="amount mono" dir="auto">${esc(payRange(r))}</div><p>${esc(originalPay(r))} · ${esc(t(r.compensation))}</p><p>${esc(conversion)}<br>FX ${dte(market.fx.date)} · ${h('Gross, before tax; not a guaranteed offer.')}</p>${!baseEligible(r)&&r.region!=='saudi'?`<p><strong>${h('Excluded from base benchmark')}</strong></p>`:''}</section>`
 +`<div class="detail-grid"><div><strong>${h('Experience')}</strong><p>${esc(expText(r))}<br>${esc(r.levelBasis||t('Not specified'))}</p></div><div><strong>${h('Role relevance')}</strong><p>${esc(reLabel(r))}<br>${h(r.collection==='automatic'?'Rule-matched feed role; review the source.':'Curated reference; check original evidence.')}</p></div>`
 +`<div class="full"><strong>${h('Scope of the role')}</strong><p>${esc(recordSummary(r))}</p><div class="chip-row">${r.skills.map(s=>badge(s)).join('')}</div></div>`
 +`<div><strong>${h('Evidence & dates')}</strong><p>${esc(r.sourceLabel)}<br>${h('Evidence date')}: ${dte(r.evidenceDate)}<br>${h('Salary evidence')}: ${dte(r.salaryVerifiedAt)}<br>${h('Published')}: ${dte(r.postedAt)}<br>${h('Last seen in feed')}: ${dte(r.lastSeenAt,true)}</p></div>`
 +`<div><strong>${h('Source status')}</strong><p>${esc(t(r.listingStatus||'Needs recheck'))}<br>${esc(r.evidenceMethod)}</p></div>`
 +`<div class="full"><strong>${h('Limitations & restrictions')}</strong><p>${esc(r.notes||'')}<br>${esc(r.restrictions||'')}</p>${r.duplicateGroup?`<div class="notice amber">${h('Client identity unconfirmed.')}</div>`:''}${r.reviewRequired?`<div class="notice amber">${h('Review required')}: ${esc(r.reviewReason||t('Needs manual review'))}</div>`:''}</div></div>`
 +`<h3>${h('Original evidence')}</h3>${link(r.sourceUrl,r.sourceUrl,'source-url')}${r.extraUrl?link(r.extraUrl,r.extraUrl,'source-url'):''}<div class="actions" style="margin-top:18px">${link(r.sourceUrl,t('Open source'),'button primary')}<button class="button" data-close="detail-dialog">${h('Close')}</button></div>`;
 $('#detail-dialog').showModal();
}
function renderTray(){
 selected=new Set([...selected].filter(id=>market.records.some(r=>r.id===id)));
 $('#compare-tray').hidden=!selected.size;
 $('#compare-label').textContent=num(selected.size)+' / 3';
 $('#compare-open').disabled=selected.size<2;
}
function compare(){
 const rows=[...selected].map(id=>market.records.find(r=>r.id===id)).filter(Boolean);
 if(rows.length<2)return;
 $('#compare-body').innerHTML=`<div class="compare-columns" style="--n:${rows.length}">`+rows.map(r=>`<article class="compare-card">${evidenceBadge(r)}<h3>${esc(r.title)}</h3><p>${esc(r.company)}<br>${esc(t(r.country))}</p><div class="money mono">SAR ${esc(payRange(r))}</div>${basisBadge(r)}<p>${esc(originalPay(r))}<br>${esc(t(r.compensation))}</p><strong>${h('EXPERIENCE')}</strong><p>${esc(expText(r))}<br>${esc(t(r.level))}</p><strong>${h('ROLE SCOPE')}</strong><p>${esc(recordSummary(r))}</p><strong>${h('LIMITATIONS')}</strong><p>${esc(r.notes)}<br>${esc(r.restrictions)}</p>${link(r.sourceUrl,t('Original source'),'text-button')}</article>`).join('')+'</div>';
 $('#compare-dialog').showModal();
}
function download(content,filename,type){const url=URL.createObjectURL(new Blob([content],{type}));const a=document.createElement('a');a.href=url;a.download=filename;document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),1500);}
function exportCSV(all=false){
 const rows=all?market.records:(['global','saudi'].includes(view)?filtered(view):market.records);
 const cols=['ID','Company','Job Title','Country','City','Role Relevance','Experience Level','Experience Required','Minimum Years','Maximum Years','Monthly Minimum SAR','Monthly Maximum SAR','Original Minimum','Original Maximum','Currency','Salary Period','Compensation','Salary Basis','Pay Basis Verified','In Base Benchmark','Evidence Type','Evidence Date','Listing Status','Source URL','Last Seen In Feed'];
 const values=rows.map(r=>[r.id,r.company,r.title,r.country,r.city,r.relevance,r.level,r.experience,r.expMin,r.expMax,monthly(r),monthly(r,'salaryMax'),r.salaryMin,r.salaryMax,r.currency,r.period,r.compensation,r.salaryBasis,r.salaryBasisVerified,baseEligible(r),r.evidenceType,r.evidenceDate,r.listingStatus,r.sourceUrl,r.lastSeenAt]);
 const quote=v=>{let s=String(v??'');if(/^[\s]*[=+@-]/.test(s))s="'"+s;return '"'+s.replace(/"/g,'""')+'"';};
 download('\ufeff'+[cols,...values].map(row=>row.map(quote).join(',')).join('\r\n'),'Knowledge_Engineering_'+(all?'All':view)+'.csv','text/csv;charset=utf-8');
 toast(t('Export CSV')+' · '+num(rows.length));
}
function saveCopy(){
 const doc=document.documentElement.cloneNode(true);
 doc.querySelector('#seed-data').textContent=JSON.stringify(market).replace(/</g,'\\u003c');
 doc.querySelectorAll('dialog').forEach(d=>d.removeAttribute('open'));
 doc.querySelector('#toast').hidden=true;doc.querySelector('#compare-tray').hidden=true;
 download('<!DOCTYPE html>\n'+doc.outerHTML,'Knowledge_Engineering_Market_Snapshot.html','text/html;charset=utf-8');
 toast(t('Saved snapshot.')+' '+t('This offline copy does not activate a live collector.'));
}
function printView(){
 $('.print-appendix')?.remove();
 const rows=['saudi','global'].includes(view)?filtered(view):view==='junior'?market.records.filter(r=>r.level==='Junior'):market.records;
 const section=document.createElement('section');section.className='print-appendix';
 section.innerHTML=`<h2>${h('Source appendix')}</h2>`+rows.map(r=>`<article><strong>${esc(r.company+' | '+r.title)}</strong><div>${esc(originalPay(r))} · SAR ${esc(payRange(r))}/${t('month')} · ${dte(r.evidenceDate)}</div>${link(r.sourceUrl,r.sourceUrl,'source-url')}</article>`).join('');
 $('#view-content').append(section);window.print();
}
async function refresh(manual=false){
 if(!['http:','https:'].includes(location.protocol)){if(manual)toast(t('This is an offline preview.'));renderShell();return;}
 if(busy)return;busy=true;$('#refresh-data').disabled=true;
 const controller=new AbortController(),timer=setTimeout(()=>controller.abort(),15000);
 try{
  const url=new URL('data/market.json',location.href);url.searchParams.set('t',String(Date.now()));
  const response=await fetch(url,{cache:'no-store',signal:controller.signal,credentials:'same-origin'});
  if(!response.ok)throw Error('HTTP '+response.status);
  const raw=await response.text();if(raw.length>8000000)throw Error('Dataset too large');
  const next=validate(JSON.parse(raw));const changed=JSON.stringify(next)!==JSON.stringify(market);
  market=next;networkMode='connected';try{localStorage.setItem(CACHE,JSON.stringify(market));}catch{}
  if(changed)mount(view);else renderShell();
  if(manual)toast(t(changed?'Published snapshot loaded.':'Already on the latest published snapshot.'));
 }catch{networkMode='failed';renderShell();if(manual)toast(t('Live refresh unavailable; keeping the previous snapshot.'));}
 finally{clearTimeout(timer);busy=false;$('#refresh-data').disabled=false;}
}
document.addEventListener('click',event=>{
 if(event.target.closest('#lang-switch')){
  lang=lang==='ar'?'en':'ar';try{localStorage.setItem(LANG_KEY,lang);}catch{}mount(view);return;
 }
 const b=event.target.closest('[data-view],[data-detail],[data-close],[data-export],[data-reset]');
 if(b?.dataset.view){mount(b.dataset.view);window.scrollTo({top:0,behavior:'instant'});}
 if(b?.dataset.detail)details(b.dataset.detail);
 if(b?.dataset.close)$('#'+b.dataset.close).close();
 if(b?.dataset.export==='csv')exportCSV();
 if(b?.dataset.export==='json')download(JSON.stringify(market,null,2),'Knowledge_Engineering_Market_Data.json','application/json');
 if(b?.dataset.reset){filters[b.dataset.reset]={...defaults};mount(view);}
 if(event.target.closest('#export-all-csv'))exportCSV(true);
});
document.addEventListener('input',event=>{if(event.target.dataset.filter==='q'&&filters[view]){filters[view].q=event.target.value;renderResults();}});
document.addEventListener('change',event=>{
 if(event.target.dataset.filter&&event.target.dataset.filter!=='q'&&filters[view]){
  filters[view][event.target.dataset.filter]=event.target.type==='checkbox'?event.target.checked:event.target.value;
  renderResults();
 }
 if(event.target.dataset.compare){
  const id=event.target.dataset.compare;
  if(event.target.checked){if(selected.size===3){event.target.checked=false;toast(t('Select up to three roles.'));return;}selected.add(id);}else selected.delete(id);
  renderTray();
 }
});
$('#compare-open').addEventListener('click',compare);
$('#compare-clear').addEventListener('click',()=>{selected.clear();renderTray();if(view==='global')renderResults();});
$('#save-snapshot').addEventListener('click',saveCopy);
$('#refresh-data').addEventListener('click',()=>refresh(true));
$('#print-view').addEventListener('click',printView);
$$('dialog').forEach(dialog=>dialog.addEventListener('click',event=>{if(event.target===dialog)dialog.close();}));
window.addEventListener('hashchange',()=>mount(location.hash.slice(1)));
window.addEventListener('online',()=>refresh());
document.addEventListener('visibilitychange',()=>{if(!document.hidden)refresh();});
setInterval(()=>{if(!document.hidden)refresh();},300000);
validate(market);mount(location.hash.slice(1)||'overview');refresh();

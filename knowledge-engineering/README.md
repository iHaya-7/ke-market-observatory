# Knowledge Engineering Workspace — دليل العمل

هذا هو مدخل أعمال KE في مرصد هيا ولبنى. المنتج التشغيلي موضح في [README الرئيسي](../README.md)؛ هذا المسار يدرس معنى المسؤوليات والرواتب والدليل والمراجعة، ويهيئ لقياس قيمة KE مقارنة بالطريقة السابقة. ملفات النموذج والرسم لا تدخل حاليًا في جمع بيانات المنتج أو بنائه.

ابدآ محليًا بـ[شرح المشروع بالعربية](00-baseline/local-corpus/project-audit/PROJECT_EXPLAINED_AR.md)، ثم [تقرير الأدلة](00-baseline/local-corpus/project-audit/PROJECT_EVIDENCE_AUDIT.md) عند الحاجة إلى التفاصيل. هذان مرجعان محميان؛ لا يُعدلان. التقارير والمراجعات تحت `local-corpus/` خاصة ومتجاهَلة في Git، وقد لا تتوفر في نسخة عامة من المستودع. [سجل تنفيذ التنظيف](00-baseline/local-corpus/project-audit/CLEANUP_EXECUTION.md) يوضح ما أزيل وما احتُفظ به.

## المراحل الموجودة فعلًا

تحديث 26 أكتوبر 2026: [Development v2 integration](07-evaluation/DEVELOPMENT_V2.md) يمدد builder وvalidator وdecision pilot لمعالجة HTML محفوظ، مع قرارات مهنية ورواتب مستقلة وأدلة قابلة للتتبع. التشغيل اختياري ومحلي؛ لا يغير التجربة المجمدة أو بيانات الموقع، ولا يثبت تحسنًا مقاسًا أو ينشئ اعتمادًا بشريًا. جدول المراحل التالي يحفظ حالة التدقيق التاريخي.

الحالة أدناه وفق تدقيق 25 أكتوبر 2026. وجود ملف أو اجتياز فحص تقني لا يعني اعتماد المعنى أو إثبات تحسن الدقة.

| المرحلة | الغرض والملفات الفعلية | الحالة وحدودها |
| --- | --- | --- |
| 0 — Baseline والتقييم | [البروتوكول](00-baseline/EVALUATION_PROTOCOL.md)، [جرد الحالات](00-baseline/CORPUS_INVENTORY.md)، [القالب](00-baseline/evaluation-template.csv)، [إغلاق التحضير](00-baseline/STAGE_0_CLOSEOUT.md)، واللقطة المعتمدة أدناه | إعداد مرجع مجمد وعينة موثق. التقييم النهائي، واعتماد الادعاءات، والأحكام البشرية المستقلة لم تكتمل |
| 1 — Scope وCQs | [SCOPE.md](01-scope/SCOPE.md)، [COMPETENCY_QUESTIONS.md](01-scope/COMPETENCY_QUESTIONS.md) | ستة أسئلة تجارية ومتطلبات إجابة؛ اعتماد المعاني وحلقة الإجابات المتوقعة/اختبارها غير مكتملين |
| 2 — Vocabulary / Metadata | [VOCABULARY.md](02-vocabulary-metadata/VOCABULARY.md)، [METADATA_DICTIONARY.md](02-vocabulary-metadata/METADATA_DICTIONARY.md)، [CQ_COVERAGE.md](02-vocabulary-metadata/CQ_COVERAGE.md) | 16 مفهومًا وتمييز بين الموجود والمقترح؛ ليست ترحيلًا لبيانات المنتج |
| 3 — Taxonomy | [role-taxonomy.ttl](03-taxonomy/role-taxonomy.ttl)، [TAXONOMY.md](03-taxonomy/TAXONOMY.md)، [TERM_MAPPING.md](03-taxonomy/TERM_MAPPING.md) | تصنيف SKOS صغير لأربعة مفاهيم مهنية؛ لا يصنف الإعلانات تلقائيًا، والاعتماد الدلالي النهائي معلق |
| 4 — Ontology | [ontology.ttl](04-ontology/ontology.ttl)، [ONTOLOGY.md](04-ontology/ONTOLOGY.md)، [CQ_TRACEABILITY.md](04-ontology/CQ_TRACEABILITY.md) | نموذج قائم: 14 class و45 خاصية مخصصة؛ التغطية التصميمية لا تثبت صحة إجابات الحالات |
| 5 — Knowledge Graph MVP | [build_graph.py](05-knowledge-graph/build_graph.py)، [الاستعلامات الخمسة](05-knowledge-graph/queries/)، [GRAPH.md](05-knowledge-graph/GRAPH.md) | تجربة موثقة على ثلاث حالات Development؛ mapping والرسم ونتائج التنفيذ الخاصة مفقودة هنا، فلا تُدّعى إعادة إنتاجها |
| 6 — SHACL / Integrity | [shapes.ttl](06-validation/shapes.ttl)، [validate_graph.py](06-validation/validate_graph.py)، [المتطلبات المحلية](06-validation/requirements-local.txt)، [VALIDATION.md](06-validation/VALIDATION.md) | فحص بنية وسلامة إسناد موثق؛ لا يثبت صحة المعنى أو أهلية الراتب. مخرجاته الخاصة غير متاحة هنا |
| 7A — Evidence triage | [ke_decision_pilot.py](07-evaluation/ke_decision_pilot.py)، [EVALUATION_READINESS.md](07-evaluation/EVALUATION_READINESS.md) | تجربة امتناع عن حسم الصلة/أهلية الراتب، وتشخيص دليل وطابور تجريبي؛ لا Before/After صالح أو تحسن مقاس |
| 7B — Development calibration | محليًا: `00-baseline/local-corpus/development/stage7b/`، و`review-export/`، و`additional-calibration/` | أحدث عمل KE تفسيري متاح: تحليلات AI ونقاشات وسجلات اتفاق. ليست Ground Truth مستقلًا أو مجموعة labels نهائية |
| 8 — Website alignment | [LUBNA_IMPLEMENTATION_REPORT.md](08-website-alignment/LUBNA_IMPLEMENTATION_REPORT.md)، وعقد الواجهة [FILTER_CONTRACT.md](../web/FILTER_CONTRACT.md) | مواءمة منتج وفلاتر؛ ليست مرحلة دلالية جديدة أو تجربة Stage 8 الموسيقية. التقرير سجل عمل مؤرخ |

قرارات النمذجة في [DECISIONS.md](DECISIONS.md). تقارير المراحل تشرح ما بُني وحدود الأدلة؛ لا تحذفوا تقرير تشغيل فريدًا لمجرد غياب مخرجاته.

## Baseline والتجربة المجمدة

المرجع المعتمد هو [20261021T110236218Z-ec7c36e4](00-baseline/snapshots/20261021T110236218Z-ec7c36e4/MANIFEST.md)، المرتبط بتنفيذ `ee5bd15`. يُحفظ مع بياناته وmanifest و`SHA256SUMS` و`verify.cjs` دون تعديل. من جذر المشروع، الفحص التالي للقراءة فقط ولا يفتح حالات Held-out:

```bash
node knowledge-engineering/00-baseline/snapshots/20261021T110236218Z-ec7c36e4/verify.cjs
```

النسخة [20261021T110343966Z-ee5bd15f](00-baseline/snapshots/20261021T110343966Z-ee5bd15f/MANIFEST.md) محفوظة كاملة **كسياق تاريخي ثانوي**؛ ليست مرجع المقارنة المعتمد. بياناتها الأربعة تطابق المرجع المعتمد، لكن manifests وتقاريرها مختلفة. لا تحذفوا أجزاءها المتكررة فتُكسر روابط الحزمة.

جرد العينة يوثق 40 حالة: 10 Development و30 Held-out، من التقاط مستقبلي منفصل عن بيانات المنتج. لا تفتحوا Held-out لتطوير القواعد أو التنظيف. البروتوكول والقوالب والأختام وتقسيم الحالات والمصادر وقرارات التعرض/المراجعة تبقى ثابتة. غياب ملفات Stage 5–7A الخاصة و`claim-specifications-v1` قيد إعادة إنتاج، وليس إذنًا بإعادة توليدها أو تغيير التجربة.

## أين تقف Stage 7B، وأين نكمل؟

توجد مراجعات مساعدة للحالات الثلاث الأولى وللسبع الباقية، واتفاقات على استبعاد الحالات الثلاث الأولى من المعيار الدولي، وثلاثة أمثلة مهنية موجبة خارج العينة المجمدة. القبول المهني لا يثبت أهلية الراتب، والمراجعة بمساعدة AI لا تصبح مرجعًا مستقلًا. الصلة العامة التي تشمل عملًا مجاورًا تختلف عن دخول معيار الرواتب الدولي المتخصص؛ والفرص السعودية تعتمد المسؤوليات دون شرط عنوان KE حرفي.

**نقطة الاستئناف: إغلاق معايرة Development بجدول قرارات واحد موثق بالإصدار والدليل والتعرض السابق لـAI.** تسجل كل منكما تفسيرها الأول ثم توثق المصالحة بين الأحكام، مع فصل الصلة وCore/Adjacent والدخول في المعيار وأهلية الراتب والحاجة إلى المراجعة. تبقى الأمثلة الخارجية منفصلة عن الحالات العشر. هذه معايرة؛ لا نعلن استقلالًا أو تحسنًا مقارنًا لم يثبت. التفاصيل في التقريرين المحميين؛ لا يلزم بدء مرحلة جديدة.

## قراءة التقارير التاريخية والمراجع

- `00-baseline/AS_IS_AUDIT.md` و`CORPUS_READINESS_REVIEW.md` و`BASELINE_INTEGRITY_RESOLUTION.md` و`CLAIM_SPECIFICATIONS_REVIEW.md` و`STAGE_0_CLOSEOUT.md` تحفظ الملاحظات والقرارات عند إعداد التجربة. مشكلة نهايات الأسطر القديمة ليست وصفًا لنتيجة الفاحص الحالية؛ لا تُغير اللقطة لإعادة كتابة التاريخ.
- [TEST_REPORT.md](../TEST_REPORT.md) و[TEST_REPORT_V3.md](../TEST_REPORT_V3.md) وتقارير المراحل وLubna تحفظ نتائج تحقق مؤرخة، لا نتائج تشغيل اليوم أو إثبات نشر حي. وجودها مقصود وليست مداخل بدء إضافية.
- مواد التعلم المحلية: [Ontology Pipeline](../learning-local/Ontology-Pipeline.md)، و[Music-KG-Training](../learning-local/Music-KG-Training/README.md). التدريب مشروع منفصل؛ الكتاب نسخة نصية محلية، وليس توثيقًا لمطابقة إصدار PDF أصلي. المراجع ignored ولا تُضمَّن في النسخة العامة.
- ملخص الحالة الحالي يبدأ بهذا الدليل والتقريرين المحميين؛ المقترحات القديمة في [CLEANUP_REVIEW.md](00-baseline/local-corpus/project-audit/CLEANUP_REVIEW.md) لا تصف الحذف المنفذ، الذي يسجله `CLEANUP_EXECUTION.md`.

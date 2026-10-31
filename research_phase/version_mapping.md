## به‌روزرسانی پس از شناسایی مخزن عمومی

ارزیابی اولیهٔ این فایل فقط بر مواد محلی تکیه داشت و بدون حذف در ادامه نگه داشته شده است. اکنون مخزن `rizwanullahmuahed2-ui/RAG-Security-Lab` در commit `6f76858df91277e4b962ee94b4286a25cfe08d4d` بررسی شده؛ ماتریس جاری به این شواهد تازه به‌روزرسانی شده است. نسخهٔ دست‌نخوردهٔ ماتریس قبلی در [initial_local_mapping.json](/workspace/research_phase/initial_local_mapping.json) و متن قبلی در [initial_local_version_mapping.md](/workspace/research_phase/initial_local_version_mapping.md) محفوظ است.

**تصحیح اصلی:** دیگر درست نیست که بگوییم تمام داده‌ها و کد A در دسترس نیست. ورودی‌های canonical شامل ۲۲۴ سند، ۲۲۵ قطعه، ۳۶۴ پرسش و ۱۰۴ حمله، legacyها، دوازده پاسخ خام WDI، manifest و کد workbench اکنون موجودند. اما آرشیف کامل اجرای اصلی ۲۱٬۸۴۰ ردیفی و کد/config دقیق وابسته به همان اجرا **در commit بررسی‌شده موجود نیست**. دسترسی به ورودی، صحت معنایی و بازاجرای تاریخی سه ادعای جدا هستند.

- تمام ۱۱۷ فایل متنی با Git blob SHA-1 و SHA-256 manifest مطابق‌اند. چهار CSV canonical با هش‌های dataset manifest مطابق‌اند؛ همهٔ روابط سند–قطعه–پرسش–حمله معتبرند.
- بازسازی خواندنیِ مستقل، مواد legacy و ۱۲ snapshot را به جدول‌های canonical field-for-field وصل کرده است. ۱۶۸ مشاهده و همهٔ ۳۳۶ مرجع WDI با مقادیر ذخیره‌شده و گردکردن half-up مطابق‌اند. این نتیجه، راستی‌آزمایی مستقل ۵۶ سند legacy یا اندازه‌گیری مستقل واقعیت‌ها نیست.
- منبع اصلی این ادعاها: [dataset_manifest.json:3](/workspace/research_phase/repo_snapshot/data/dataset_manifest.json:3) · [commit-pinned source](https://github.com/rizwanullahmuahed2-ui/RAG-Security-Lab/blob/6f76858df91277e4b962ee94b4286a25cfe08d4d/data/dataset_manifest.json#L3-L8)؛ [build_dataset.py:44](/workspace/research_phase/repo_snapshot/scripts/build_dataset.py:44) · [commit-pinned source](https://github.com/rizwanullahmuahed2-ui/RAG-Security-Lab/blob/6f76858df91277e4b962ee94b4286a25cfe08d4d/scripts/build_dataset.py#L44-L100)؛ [گزارش audit داده](/workspace/research_phase/repo_audit/original_data_audit.json:10).

### چه چیزی هنوز بازیابی نشده است؟

README تصریح می‌کند که `results/runs/` نادیده گرفته می‌شود و runهای تاریخی commit نشده‌اند. مستند مقاله نیز می‌گوید کد فعلی، کپی ثابت اجرای تاریخی نیست. بنابراین وجود repo یا امکان اجرای app، گواه بازتولید ارقام قدیمی نیست. [README.md:55](/workspace/research_phase/repo_snapshot/README.md:55) · [commit-pinned source](https://github.com/rizwanullahmuahed2-ui/RAG-Security-Lab/blob/6f76858df91277e4b962ee94b4286a25cfe08d4d/README.md#L55-L69)؛ [README.md:23](/workspace/research_phase/repo_snapshot/research/README.md:23) · [commit-pinned source](https://github.com/rizwanullahmuahed2-ui/RAG-Security-Lab/blob/6f76858df91277e4b962ee94b4286a25cfe08d4d/research/README.md#L23-L29).

کد فعلی `hashing-lexical-v2` و `extractive-evidence-v2` است و بودجه‌های پیش‌فرض ۰/۱۰/۲۰/۵۰/۱۰۴ دارد؛ مقالهٔ تاریخی بودجه‌های ۰/۱۰/۳۰/۶۰/۱۰۴ و backend قدیمی را گزارش می‌کند. در نتیجه اجرای تازهٔ defaultها، بازاجرای خودکار مطالعهٔ اصلی نخواهد بود. [config.yaml:1](/workspace/research_phase/repo_snapshot/config.yaml:1) · [commit-pinned source](https://github.com/rizwanullahmuahed2-ui/RAG-Security-Lab/blob/6f76858df91277e4b962ee94b4286a25cfe08d4d/config.yaml#L1-L39)؛ [llm_interface.py:39](/workspace/research_phase/repo_snapshot/src/generation/llm_interface.py:39) · [commit-pinned source](https://github.com/rizwanullahmuahed2-ui/RAG-Security-Lab/blob/6f76858df91277e4b962ee94b4286a25cfe08d4d/src/generation/llm_interface.py#L39-L48).

### مواد validation با اجرای اصلی یکی نیستند

پوشهٔ commitشدهٔ `results/targeted-mode-validation/` یک diagnostic جدا با ۳۶۴ سؤال، assertionهای مصنوعیِ مخصوص هر سؤال، صفر/ده نسخه و مجموع ۱٬۰۹۲ ردیف است. summary آن نتایج ۳۵۵/۳۳۷/۳۵۵ و ۲۷ حمله را گزارش می‌کند؛ این نه آرشیف اصلی ۲۱٬۸۴۰ ردیفی است، نه مطالعهٔ تکرار/جعل برچسب ۳٬۰۱۶ ردیفی، و نه آزمایش LLM محلی B. [summary.json:3](/workspace/research_phase/repo_snapshot/results/targeted-mode-validation/summary.json:3) · [commit-pinned source](https://github.com/rizwanullahmuahed2-ui/RAG-Security-Lab/blob/6f76858df91277e4b962ee94b4286a25cfe08d4d/results/targeted-mode-validation/summary.json#L3-L35).

چهار هش CSV در summary diagnostic با bytes فعلی LF متفاوت است، ولی هر چهار دقیقاً با تبدیل همان bytes به CRLF مطابق می‌شود. این تفاوت خط پایان را نباید تغییر factual داده نامید. در عین حال، شش ماژول source نسبت به snapshot diagnostic عوض شده‌اند؛ نسخه‌ها باید جدا بمانند. [مقایسهٔ source](/workspace/research_phase/repo_audit/diagnostic_source_hash_comparison.json:1).

### نسخهٔ مقاله و محدودهٔ مطالعهٔ مولد

PDF واقعی مخزن از طریق connector بررسی شد: ۱۸ صفحه با SHA-256 `87059e66898a6aaecede4d4d8224e2de97ed045f79b822eb2d903fbd3cc7533f`، همان فایل اصلی است. مقالهٔ نهایی محلی ۱۶ صفحه و فایل جدا است. این امر ابهام نسخه را مشخص‌تر می‌کند، اما ثابت نمی‌کند متخصص کدام فایل را دریافت کرده است. [شناسهٔ نسخه‌ها](/workspace/research_phase/version_identification.json:1)؛ [manifest.json:11](/workspace/research_phase/repo_snapshot/research/manifest.json:11) · [commit-pinned source](https://github.com/rizwanullahmuahed2-ui/RAG-Security-Lab/blob/6f76858df91277e4b962ee94b4286a25cfe08d4d/research/manifest.json#L11-L20).

مخزن، یک مسیر اختیاری Anthropic را مستند می‌کند و اجرای generative را برای validation موجود تأیید نمی‌کند. از آن نباید نتیجه گرفت آزمایش محلی OpenAI با ۶۴ سؤال/۳۷۶ درخواست در repo منتشر یا بازتولید شده است. [README.md:25](/workspace/research_phase/repo_snapshot/research/README.md:25) · [commit-pinned source](https://github.com/rizwanullahmuahed2-ui/RAG-Security-Lab/blob/6f76858df91277e4b962ee94b4286a25cfe08d4d/research/README.md#L25-L29)؛ [EXPERIMENTS.md:86](/workspace/research_phase/repo_snapshot/docs/EXPERIMENTS.md:86) · [commit-pinned source](https://github.com/rizwanullahmuahed2-ui/RAG-Security-Lab/blob/6f76858df91277e4b962ee94b4286a25cfe08d4d/docs/EXPERIMENTS.md#L86-L96).

### بازبینی محاسباتی B در مرحلهٔ ریسرچ

یک audit جداگانهٔ خواندنی، تمام ۱٬۲۸۰ فهرست نامزد، زمینهٔ نهایی و payload را از بردارهای ذخیره‌شده بازسازی و نمره‌ها و انتقال‌های جفتی را دوباره محاسبه کرده است؛ اختلاف حسابی با آرشیف ثبت نشده است. نمونه‌های واقعیِ نیازمند بررسی معنایی نیز اکنون در یادداشت audit موجودند. این کار فراخوانی تازهٔ مدل، بازاجرای A یا داوری انسانی نیست. فایل‌های منجمد اصلی تغییر نکرده‌اند. [گزارش audit](/workspace/research_phase/artifact_audit/audit_report.md:5).

### نتیجه برای پلان بعدی

بخشی از کار که قبلاً «مواد در دسترس نیست» بود، اکنون به «مواد ورودی موجود و قابل بررسی» تبدیل شده است. متن availability مقاله باید در مرحلهٔ مجازِ ویرایش تصحیح شود؛ اکنون هیچ مقاله یا نتیجه‌ای تغییر داده نشده است. هنوز سند proposal اصلی، تصمیم‌های واقعی بازبین انسانی، آرشیف اصلی run، آرشیف کامل تکرار/جعل labels و آزمایش چنددوزی مولد فراهم نشده‌اند. انتخاب اهداف، scoring و metadata باید بر اساس نسخهٔ مشخص بررسی شوند، نه با مخلوط‌کردن مراحل.

ماتریس ۶۷بندی جاری شامل 25 ردیف پاسخ‌داده‌شده، 39 ردیف بخشی پاسخ‌داده‌شده، 2 ردیف فاقد شاهد تکمیل‌شده و 1 ردیف با مواد مشخصِ هنوز غایب است. این شمارش، نمرهٔ اعتبار علمی یا تأیید آمادگی نشر نیست.

---

## ارزیابی اولیهٔ محلی — ثبت تاریخی، پیش از شناسایی مخزن

# تطبیق گزارش متخصص با آخرین مقاله و شواهد موجود

این یادداشت فقط حاصل مرحلهٔ ریسرچ و بررسی اسناد است. مقاله، آزمایش‌های ثابت، پاسخ‌های API و نمره‌ها تغییر نکرده‌اند. هیچ فراخوانی مدل یا آزمایش تازه‌ای انجام نشده است.

## نتیجهٔ اصلی

مقالهٔ فعلی بخشی از نقدها را پاسخ داده است: معماری استخراجی و مولد را جدا می‌کند، آزمایش واقعی LLM و کنترل‌های همسان دارد، روش و مخرج معیارها را بیان می‌کند و ادعاها را محدود نگه می‌دارد. اما این پیشرفت با بازتولید آزمایش تاریخی یا صحت‌سنجی معنایی مستقل یکسان نیست.

- **Study A:** داده‌ها و کد اصلیِ ۲۲۴ سند، ۳۶۴ پرسش و ۱۰۴ هدف در دسترس نیست. خود مقاله این مرز را بیان می‌کند: [روش، خط ۹۱](/workspace/revision/Revised_Manuscript.md:91) و [پیوست B، خط ۳۴۲](/workspace/revision/Revised_Manuscript.md:342). ارقام و نمودارهای A شواهد تاریخیِ نقل‌شده‌اند، نه نتایج تازه بازاجراشده.
- **Study B:** ۶۴ پرسش، ۶۴ پرسش اهداکنندهٔ کنترل، ۶۴۰ قطعه، ۱۹۲ متن درج‌شده، ۳۷۶ پاسخ متفاوت و ۱٬۲۸۰ ردیف شرطی واقعاً موجود است. این گسترشِ تازه، بازاجرای A نیست: [روش، خط ۹۳](/workspace/revision/Revised_Manuscript.md:93).
- تمام هفت هش ورودی B و هش‌های زمینه، درخواست و پاسخ در این بررسی خواندنی مطابق بودند. این تطابق، انسجام داخلی بسته را نشان می‌دهد؛ اصالت منابع، صحت مرجع یا تأیید معنایی پاسخ را به‌تنهایی ثابت نمی‌کند. [freeze.json](/workspace/revision/experiment/freeze.json:5)، [generation_freeze.json](/workspace/revision/experiment/generation_freeze.json:5).
- **هیچ داوری انسانی تکمیل نشده است:** هر ۳۷۶ ردیف فایل بازبینی، در هر سه ستون داوری خالی است. الگو و راهنما موجودند، اما نتیجهٔ داوری نیستند. [فایل راهنما](/workspace/revision/experiment/HUMAN_REVIEW_INSTRUCTIONS.md:1) و [analysis.json](/workspace/revision/experiment/analysis.json:23).
- **آزمایش چندبودجه‌ای با اهداف ثابت برای LLM انجام نشده است:** B تنها یک درج برای هر هدف دارد. ثابت‌بودن ۶۴ هدف در یک سطح مثبت، جای sweep چندسطحی را نمی‌گیرد. [تنظیمات](/workspace/revision/experiment/config.json:30) و [مقاله](/workspace/revision/Revised_Manuscript.md:267).

## ابهام نسخهٔ بررسی‌شده

گزارش متخصص روی backend استخراجی و ارقام تاریخی متمرکز است و هیچ اشاره‌ای به HotpotQA، GPT-4.1 mini، ۳۷۶ درخواست یا آزمایش ۶۴پرسشی ندارد. این نکته نیاز به تطبیق نسخه دارد؛ اما ثابت نمی‌کند که متخصص فایل اشتباهی گرفته است، چون مقالهٔ نهایی نیز Study A را نگه داشته است. در برنامهٔ بعدی باید نسخه/هش فایل بررسی‌شده روشن و هر نقد به A، B یا هر دو وصل شود.

## شکاف‌هایی که با ویرایش متن بسته نمی‌شوند

۱. **بازآزمایی A:** فهرست منابع قدیمی، ۱۲ شاخص، ۱۰۴ حمله، پاسخ‌ها، خروجی‌ها، configها و کد تاریخی باید واقعاً بازیابی شوند. مسیرهایی که در گزارش قبلی ذکر شده‌اند اکنون وجود ندارند؛ متن PDF یا تصویر منحنی، جای فایل خام را نمی‌گیرد.

۲. **بررسی معنایی:** نمونهٔ واقعی بازبین‌های مستقل، تصمیم‌های ثبت‌شده، اختلاف‌ها و تطبیق با معیار خودکار لازم است. نمره‌گذاری AI را نباید داوری انسانی نامید.

۳. **تحلیل موردی:** در [scored_results.csv:8](/workspace/revision/experiment/scored_results.csv:8) پاسخ سال ۱۹۷۲ را ذکر می‌کند ولی صریحاً UNKNOWN و نبود شاهد را نیز می‌گوید؛ معیار عددی آن را gold-only شمرده است. این مثال، دلیل عملی برای بازبینی معنایی است، نه مجوز تغییر پنهانی معیار پس از دیدن خروجی‌ها.

۴. **دوز ثابت با چند سطح:** یک پروتکل جدا با پوشش ثابت اهداف، تعداد نسخه/تنوع متن/بودجهٔ توکن و سهم آلودگی روشن لازم است. baseline موجود قبلاً دیده شده؛ ادامهٔ آن نباید به عنوان آزمون کاملاً دست‌نخورده معرفی شود.

۵. **حاکمیت اعتماد:** برچسب‌های B به‌صورت مصنوعی در کد تعیین شده‌اند. تغییر مستقیم این فیلدها با دورزدن احراز اصالت یا کنترل دسترسی واقعی یکی نیست. اگر ادعای عملیاتی حفظ شود، مرجع تأیید، روند، کنترل و log واقعی لازم است؛ در غیر آن باید آزمایش به همان boundary فرض‌شده محدود بماند.

۶. **رابطه با طرح اولیه:** تفاوت ChromaDB/embedding/LLMِ توصیف‌شده با اجرای تاریخی روشن است، اما سند پیشنهاد اصلی و علت تصمیم‌های اجرایی وجود ندارد. محدودیت مالی، سخت‌افزار یا fallback نباید بدون سند ساخته شود.

## قید پیشنهادها و حدود بسته

آزمایش LLM در گزارش متخصص مشروط به حفظ ادعای LLM-RAG است؛ این بخش برای B انجام شده. بازبینی انسانی و آزمون دستکاری غیرمجاز metadata در بعضی بندها با «در صورت امکان» آمده‌اند؛ آزمایش اهداف ثابت در همهٔ دوزها با «بهتر است» پیشنهاد شده است. این قیدها باید حفظ شوند، اما جایگزین شواهد تکمیل‌نشده نیستند.

نسخهٔ کامل Parquet منبع B در cache فعلی /tmp وجود ندارد؛ URL پین‌شده و SHA-256 آن در بسته هست. قبل از ادعای بازسازی مستقل انتخاب داده، فایل upstream باید بازیابی، هش‌سنجی و خروجی انتخاب دوباره مقایسه شود. نسخه‌های نرم‌افزار ثبت شده‌اند؛ سند تاریخ‌دار OS/CPU/RAM/معماری کلاینت در بسته نیست. سخت‌افزار دوردست ارائه‌دهندهٔ مدل نیز گزارش نشده است.

## ماتریس پوشش درخواست‌ها

ماتریس JSON برای هر بند، دامنهٔ A/B، نوع درخواست، قید الزامی/پیشنهادی، شاهد دارای خط، ارزیابی و مدرک لازم برای بستن شکاف را ثبت می‌کند. ۶۷ ردیف، چک‌لیست پوشش است؛ تعداد ردیف‌های «پاسخ‌داده‌شده» معیار کیفیت علمی یا اجازهٔ نشر نیست.

| بند | درخواست | وضعیت | شاهد اصلی |
|:--|:--|:--|:--|
| 3.1.1 | State the architecture actually executed | بخشی پاسخ داده شده | [Revised_Manuscript.md:91](/workspace/revision/Revised_Manuscript.md:91) |
| 3.1.2 | Explain why hashing and TF-IDF were chosen and how they differ from the original design | فاقد شاهد تکمیل‌شده | [Revised_Manuscript.md:99](/workspace/revision/Revised_Manuscript.md:99) |
| 3.1.3 | Explain why proposed vector database, neural embeddings, or LLM components were inactive | مواد اصلی در دسترس نیست | [source_original_article.txt:817](/workspace/revision/source_original_article.txt:817) |
| 3.1.4 | Execute at least one real LLM experiment if retaining LLM-RAG claims | پاسخ داده شده | [Revised_Manuscript.md:149](/workspace/revision/Revised_Manuscript.md:149) |
| 3.1.5 | Otherwise narrow title, abstract, and conclusion to the system actually tested | پاسخ داده شده | [Revised_Manuscript.md:18](/workspace/revision/Revised_Manuscript.md:18) |
| 3.2.1 | Provide the original source-document list | بخشی پاسخ داده شده | [Revised_Manuscript.md:91](/workspace/revision/Revised_Manuscript.md:91) |
| 3.2.2 | Document selection of 168 WDI observations and indicator families | مواد اصلی در دسترس نیست | [Revised_Manuscript.md:248](/workspace/revision/Revised_Manuscript.md:248) |
| 3.2.3 | Specify document, chunk, question, and answer schemas | بخشی پاسخ داده شده | [prepare_experiment.py:101](/workspace/revision/experiment/prepare_experiment.py:101) |
| 3.2.4 | Explain how the 364 historical questions were generated: manual, automatic, or mixed | مواد اصلی در دسترس نیست | [Revised_Manuscript.md:248](/workspace/revision/Revised_Manuscript.md:248) |
| 3.2.5 | Explain and demonstrate verification of questions and reference answers | بخشی پاسخ داده شده | [prepare_experiment.py:49](/workspace/revision/experiment/prepare_experiment.py:49) |
| 3.2.6 | State whether inherited documents and trust labels were re-audited | بخشی پاسخ داده شده | [source_original_article.txt:250](/workspace/revision/source_original_article.txt:250) |
| 3.2.7 | Make source-document, chunk, and question relationships traceable | بخشی پاسخ داده شده | [prepare_experiment.py:100](/workspace/revision/experiment/prepare_experiment.py:100) |
| 3.2.8 | Account for correlated question formulations and shared facts in uncertainty | بخشی پاسخ داده شده | [Revised_Manuscript.md:73](/workspace/revision/Revised_Manuscript.md:73) |
| 3.3.1 | Release all 104 historical target questions | مواد اصلی در دسترس نیست | [Revised_Manuscript.md:91](/workspace/revision/Revised_Manuscript.md:91) |
| 3.3.2 | Release the correct answer for each historical target | مواد اصلی در دسترس نیست | [Revised_Manuscript.md:91](/workspace/revision/Revised_Manuscript.md:91) |
| 3.3.3 | Release the attacker-selected false value for each historical target | مواد اصلی در دسترس نیست | [Revised_Manuscript.md:91](/workspace/revision/Revised_Manuscript.md:91) |
| 3.3.4 | Release the complete text of every historical poison passage | مواد اصلی در دسترس نیست | [Revised_Manuscript.md:91](/workspace/revision/Revised_Manuscript.md:91) |
| 3.3.5 | Provide the original-source identifier linked to each historical attack | مواد اصلی در دسترس نیست | [Revised_Manuscript.md:91](/workspace/revision/Revised_Manuscript.md:91) |
| 3.3.6 | Provide trust labels used for each attack condition | بخشی پاسخ داده شده | [config.json:33](/workspace/revision/experiment/config.json:33) |
| 3.3.7 | Explain the attack-generation process | بخشی پاسخ داده شده | [Revised_Manuscript.md:143](/workspace/revision/Revised_Manuscript.md:143) |
| 3.3.8 | Describe attack length, structure, vocabulary, and similarity to clean material | بخشی پاسخ داده شده | [Revised_Manuscript.md:143](/workspace/revision/Revised_Manuscript.md:143) |
| 3.4.1 | Explain exact answer-value scoring with examples | بخشی پاسخ داده شده | [Revised_Manuscript.md:63](/workspace/revision/Revised_Manuscript.md:63) |
| 3.4.2 | Specify numeric, year, unit, decimal, and format normalization | بخشی پاسخ داده شده | [analyze_experiment.py:36](/workspace/revision/experiment/analyze_experiment.py:36) |
| 3.4.3 | Recheck results against references with executable scoring | بخشی پاسخ داده شده | [analyze_experiment.py:65](/workspace/revision/experiment/analyze_experiment.py:65) |
| 3.4.4 | Show correct, incorrect, and ambiguous automatic-scoring examples | بخشی پاسخ داده شده | [Revised_Manuscript.md:242](/workspace/revision/Revised_Manuscript.md:242) |
| 3.4.5 | Compare a human-reviewed sample with automatic judgments | فاقد شاهد تکمیل‌شده | [Revised_Manuscript.md:171](/workspace/revision/Revised_Manuscript.md:171) |
| 3.4.6 | Separate correct-source retrieval, answer selection, and generative answer correctness | پاسخ داده شده | [Revised_Manuscript.md:63](/workspace/revision/Revised_Manuscript.md:63) |
| 3.5.1 | Analyze retrieval, answer selection, and attack success separately | پاسخ داده شده | [Revised_Manuscript.md:63](/workspace/revision/Revised_Manuscript.md:63) |
| 3.5.2 | Explain why more gold recall can coexist with lower answer accuracy | بخشی پاسخ داده شده | [Revised_Manuscript.md:217](/workspace/revision/Revised_Manuscript.md:217) |
| 3.5.3 | Analyze failure cases rather than only endpoint numbers | بخشی پاسخ داده شده | [Revised_Manuscript.md:217](/workspace/revision/Revised_Manuscript.md:217) |
| 3.5.4 | Bound conclusions and do not interpret zero ASR as universal immunity | پاسخ داده شده | [Revised_Manuscript.md:153](/workspace/revision/Revised_Manuscript.md:153) |
| 3.6.1 | Explain how trust labels are assigned | بخشی پاسخ داده شده | [Revised_Manuscript.md:85](/workspace/revision/Revised_Manuscript.md:85) |
| 3.6.2 | Identify the person or institution authorized to approve documents | فاقد شاهد تکمیل‌شده | [Revised_Manuscript.md:85](/workspace/revision/Revised_Manuscript.md:85) |
| 3.6.3 | Clarify whether metadata is backed by authentication, audit logging, and access control | پاسخ داده شده | [Revised_Manuscript.md:85](/workspace/revision/Revised_Manuscript.md:85) |
| 3.6.4 | Include the gate limitation in discussion and conclusion | پاسخ داده شده | [Revised_Manuscript.md:297](/workspace/revision/Revised_Manuscript.md:297) |
| 3.6.5 | Where possible test unauthorized metadata modification and its impact | بخشی پاسخ داده شده | [Revised_Manuscript.md:85](/workspace/revision/Revised_Manuscript.md:85) |
| 3.7.1 | Document target selection at each attack budget | بخشی پاسخ داده شده | [source_original_article.txt:321](/workspace/revision/source_original_article.txt:321) |
| 3.7.2 | Separate attacked-target coverage, success count, and success rate among attacked targets | پاسخ داده شده | [Revised_Manuscript.md:73](/workspace/revision/Revised_Manuscript.md:73) |
| 3.7.3 | Add fixed-target evaluation across multiple attack doses | بخشی پاسخ داده شده | [Revised_Manuscript.md:267](/workspace/revision/Revised_Manuscript.md:267) |
| 3.7.4 | Document seed values, use, and influence on selection | بخشی پاسخ داده شده | [source_original_article.txt:322](/workspace/revision/source_original_article.txt:322) |
| 3.8.1 | Analyze cases with retrieved correct evidence but wrong final answers | بخشی پاسخ داده شده | [Revised_Manuscript.md:217](/workspace/revision/Revised_Manuscript.md:217) |
| 3.8.2 | Analyze exposed poison when the attack nevertheless fails | بخشی پاسخ داده شده | [Revised_Manuscript.md:217](/workspace/revision/Revised_Manuscript.md:217) |
| 3.8.3 | Analyze attack prevention without correct-answer restoration | بخشی پاسخ داده شده | [Revised_Manuscript.md:79](/workspace/revision/Revised_Manuscript.md:79) |
| 3.8.4 | Analyze how changed trust labels change attack outcomes | پاسخ داده شده | [Revised_Manuscript.md:225](/workspace/revision/Revised_Manuscript.md:225) |
| 3.8.5 | Analyze repetition-induced changes in system behavior | مواد اصلی در دسترس نیست | [Revised_Manuscript.md:275](/workspace/revision/Revised_Manuscript.md:275) |
| 3.8.6 | Present repetition as a separate protocol with complete execution and evaluation detail | بخشی پاسخ داده شده | [Revised_Manuscript.md:275](/workspace/revision/Revised_Manuscript.md:275) |
| 4.1 | Abstract: problem, actual method, data, major results, and main limitation | پاسخ داده شده | [Revised_Manuscript.md:18](/workspace/revision/Revised_Manuscript.md:18) |
| 4.2 | Methods sufficiently detailed to reconstruct the entire pipeline | بخشی پاسخ داده شده | [Revised_Manuscript.md:113](/workspace/revision/Revised_Manuscript.md:113) |
| 4.3 | Results: precise metrics/conditions and separation of principal and supplementary experiments | پاسخ داده شده | [Revised_Manuscript.md:173](/workspace/revision/Revised_Manuscript.md:173) |
| 4.4 | Discussion: explain retrieval/attack divergence and metadata limitations | بخشی پاسخ داده شده | [Revised_Manuscript.md:285](/workspace/revision/Revised_Manuscript.md:285) |
| 4.5 | Conclusion restricted to directly supported experimental claims | پاسخ داده شده | [Revised_Manuscript.md:303](/workspace/revision/Revised_Manuscript.md:303) |
| 5.1 | Full preparation/retrieval/reranking/filtering/scoring code | بخشی پاسخ داده شده | [README.md:27](/workspace/revision/experiment/README.md:27) |
| 5.2 | Original documents, chunks, questions, and reference answers | بخشی پاسخ داده شده | [README.md:30](/workspace/revision/experiment/README.md:30) |
| 5.3 | Complete attack passages, IDs, targets, and desired false answers | بخشی پاسخ داده شده | [insertions.json:1](/workspace/revision/experiment/insertions.json:1) |
| 5.4 | Complete experimental configuration and seeds | بخشی پاسخ داده شده | [config.json:3](/workspace/revision/experiment/config.json:3) |
| 5.5 | Raw per-question/per-defense/per-dose outcomes | بخشی پاسخ داده شده | [README.md:36](/workspace/revision/experiment/README.md:36) |
| 5.6 | Executable Recall/accuracy/ASR/exposure evaluator | بخشی پاسخ داده شده | [analyze_experiment.py:36](/workspace/revision/experiment/analyze_experiment.py:36) |
| 5.7 | Software, hardware, and environment information | بخشی پاسخ داده شده | [generation_freeze.json:10](/workspace/revision/experiment/generation_freeze.json:10) |
| 5.8 | Data-source provenance, extraction, access dates, and verification records | بخشی پاسخ داده شده | [source_dataset_metadata.json:2](/workspace/revision/experiment/source_dataset_metadata.json:2) |
| 5.9 | Explain proposed versus actually executed architecture | بخشی پاسخ داده شده | [Revised_Manuscript.md:91](/workspace/revision/Revised_Manuscript.md:91) |
| 5.10 | Documentation for trust-label and repetition supplementary experiments | بخشی پاسخ داده شده | [run_experiment.py:145](/workspace/revision/experiment/run_experiment.py:145) |
| 5.11 | Explain publication/licensing restrictions and share publishable materials | بخشی پاسخ داده شده | [README.md:76](/workspace/revision/experiment/README.md:76) |
| 6.1 | First clarify the real methodology and used components | بخشی پاسخ داده شده | [Revised_Manuscript.md:87](/workspace/revision/Revised_Manuscript.md:87) |
| 6.2 | Then recompute and reproduce existing results from code and raw data | بخشی پاسخ داده شده | [Revised_Manuscript.md:91](/workspace/revision/Revised_Manuscript.md:91) |
| 6.3 | Then improve evaluation, review a human sample, and report justified uncertainty | بخشی پاسخ داده شده | [Revised_Manuscript.md:167](/workspace/revision/Revised_Manuscript.md:167) |
| 6.4 | Then perform real-LLM supplementary experiments under matched conditions and fixed-target doses | بخشی پاسخ داده شده | [Revised_Manuscript.md:157](/workspace/revision/Revised_Manuscript.md:157) |
| 6.5 | Finally rewrite abstract/discussion/conclusion from verified results and remove unsupported claims | پاسخ داده شده | [Revised_Manuscript.md:18](/workspace/revision/Revised_Manuscript.md:18) |

## نقطهٔ شروع مناسب برای پلان بعدی

اول تطبیق نسخه و موجودی شواهد؛ سپس تعیین سرنوشت ادعاهای A بر اساس دسترسی واقعی به آرشیف؛ بعد بازنمره‌دهی و replay خواندنی B در یک محل جدا؛ سپس طراحی داوری انسانی و تحلیل شکست؛ و در صورت توجیه، پروتکل آزمایش تکمیلی با اهداف ثابت. بازنویسی نهایی باید پس از این تصمیم‌ها و شواهد بیاید، نه قبل از آن.

فایل دقیق ماشین‌خوان: [gap_matrix.json](/workspace/research_phase/gap_matrix.json).

## نکتهٔ ویرایشی جدا از شکاف‌های علمی

در [مرجع ۱۴، خط ۳۷۲ مقاله](/workspace/revision/Revised_Manuscript.md:372)، عبارت سربرگ «RAG SECURITY RESEARCH» به انتهای مرجع چسبیده است؛ این ظاهراً اثر استخراج متن از PDF است. این مورد فقط برای copyediting بعدی ثبت شد و اصلاح نشده است.

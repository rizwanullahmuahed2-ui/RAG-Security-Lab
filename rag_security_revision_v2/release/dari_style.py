"""Apply the author's Dari wording and unambiguous number display to prose.

Code spans, fenced commands and URLs are preserved. Scientific source files and
frozen experiment records are not edited by this formatter.
"""
import re

_DIGITS = str.maketrans('0123456789.', '۰۱۲۳۴۵۶۷۸۹٫')

def dari_text(text):
    saved = []
    def hold(match):
        saved.append(match.group(0))
        return f'@@PROTECTED_{len(saved)-1}@@'
    text = re.sub(r'```[\s\S]*?```|`[^`\n]+`|https?://[^\s<>)]+', hold, text)
    # Preserve verbal uses of داده while replacing the noun meaning data.
    verbs = []
    def verb(match):
        verbs.append(match.group(0))
        return f'@@VERB_{len(verbs)-1}@@'
    text = re.sub(r'(?:نشان|قرار|پاسخ|ارائه|نمره)\s+داده(?:\u200c(?:اند|است))?', verb, text)
    for old,new in [
        ('داده‌شده','ارائه‌شده'),('داده شده','ارائه شده'),
        ('داده می‌شود','ارائه می‌شود'),('داده می‌شوند','ارائه می‌شوند'),
        ('داده نشده','ارائه نشده'),
        ('فراداده','میتادیتا'),('پایگاه داده','پایگاه دیتا'),
        ('مجموعهٔ داده','مجموعهٔ دیتا'),('مجموعه داده','مجموعهٔ دیتا'),
        ('داده‌های','دیتای'),('داده‌ها','دیتا'),
        ('دادهٔ','دیتای'),('دیتأ','دیتای'),
        ('پرونده','فایل'),('اطلاعات','معلومات'),('کنترل','کنترول'),
        ('سامانه','سیستم'),('پیوند','لینک'),
        ('سیستمٔ','سیستم'),('فایلٔ','فایل'),('مخزن','ریپو'),
        ('درصد','فیصد'),('اعشاری','اشاری'),('آرشیو','آرشیف'),
        ('بایگانی','آرشیف'),('آزمون','آزمایش'),('پیکربندی','تنظیمات'),
        ('فرایند','روند'),('فرآیند','روند'),('کارایی','کارکرد'),
        ('راستی‌آزمایی','بررسی صحت'),('آماده‌سازی','آماده‌ساختن'),
        ('ردیف','سطر'),
        ('سطر‌های','سطرهای'),
    ]:
        text = text.replace(old,new)
    text = re.sub(r'(?<![\w\u200c])داده(?![\w\u200c]|\s+(?:شده|شود|شد|می|است|اند|بود|باشد|باشند))', 'دیتا', text)
    # Counts have no thousands marker; decimal values keep their decimal mark.
    text = re.sub(r'(?<=\d)[\u066c\u2019\u2018\'](?=\d{3}(?:\D|$))', '', text)
    text = re.sub(r'(?<=\d),(?=\d{3}(?:\D|$))', '', text)
    text = re.sub(r'([0-9۰-۹]+(?:[.٫][0-9۰-۹]+)?)\s*[٪%]',
                  lambda m: m.group(1).translate(_DIGITS)+' فیصد', text)
    for i,value in enumerate(verbs):
        text = text.replace(f'@@VERB_{i}@@', value)
    for i,value in enumerate(saved):
        text = text.replace(f'@@PROTECTED_{i}@@', value)
    return text

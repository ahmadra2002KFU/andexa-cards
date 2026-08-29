# Andexa Cards

بطاقات العمل الإلكترونية لفريق أنديكسا — تعمل عبر NFC وQR.
كل بطاقة على رابط: **`card.andexa.tech/<slug>`** (مثال: card.andexa.tech/meshari).

## أضف بطاقتك بنفسك

1. أنشئ مجلدًا باسمك داخل `people/` — بالإنجليزية وبأحرف صغيرة (هذا يصبح رابطك).
2. انسخ `people/meshari/card.json` إلى مجلدك وعدّل كل الحقول.
3. أضف صورتك باسم `photo.jpg` (اختياري — بدونها يظهر حرف اسمك). يُفضَّل صورة مربعة للوجه؛ البناء يضغطها تلقائيًا.
4. ادفع إلى `main` (أو افتح Pull Request). GitHub Actions يبني وينشر تلقائيًا خلال دقيقة.

ملف `card.json` — كل الحقول مطلوبة عدا الصورة:

| الحقل | المعنى |
|---|---|
| `name_en` / `name_ar` | الاسم المعروض على البطاقة |
| `full_name_en` | الاسم الكامل (يُحفظ في جهات الاتصال) |
| `vcard.family/given/middle` | تقسيم الاسم لملف vCard |
| `phonetic_first_ar` / `phonetic_last_ar` | الاسم العربي (يظهر في جهات الاتصال كنطق) |
| `title_en` / `title_ar` | المسمّى الوظيفي |
| `phone` | بصيغة دولية `+9665xxxxxxxx` |
| `whatsapp` | نفس الرقم بدون `+` |
| `email`, `website`, `linkedin` | الروابط |
| `monogram_en` / `monogram_ar` | حرف يظهر مكان الصورة إن لم توجد |

## كيف يعمل

- `tools/build.py` يقرأ `people/*/card.json` ويولّد `site/`: صفحة لكل شخص + ملف vCard (بالصورة مضمّنة إن وُجدت) + فهرس في الجذر.
- `.github/workflows/deploy.yml` يبني عند كل دفعة وينشر `site/` إلى فرع `gh-pages` (GitHub Pages).
- النطاق: ملف `CNAME` يتولد تلقائيًا بـ`card.andexa.tech`؛ سجل Cloudflare: ‏CNAME‏ `card` → `ahmadra2002kfu.github.io` بوضع DNS only.

## تشغيل محلي

```
pip install pillow
python tools/build.py
python -m http.server 5602 --directory site
```

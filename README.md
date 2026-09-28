# Manage Cloud - MySQL Database Manager

A PyQt6-based MySQL database manager with SSH tunneling support.

## محتويات المستودع / Repository Contents

يحتوي هذا المستودع على نسختين نظيفتين للتطبيق:

### 1. `Manage_Cloud_App/` (البرنامج الجاهز للتشغيل)
نسخة تنفيذية كاملة بصيغة `main.exe` جاهزة للتشغيل المباشر على أنظمة Windows 64-bit دون الحاجة لتثبيت بايثون:
- يحتوي على ملف `main.exe`.
- ملف `.env` فارغ من أية بيانات اتصال جاهز لتدخل فيه بياناتك.
- الثيم وملفات التنسيق `assets/`.
- دليل استخدام باللغة العربية (`تعليمات_التشغيل.txt`).

### 2. `Manage_Cloud_Source/` (الكود المصدري)
الكود المصدري الكامل للمشروع للمطورين:
- مبني بلغة بايثون وواجهة PyQt6.
- كود نظيف وخالٍ من ملفات الكاش والبيانات الحساسة.
- لتثبيت المتطلبات: `pip install -r requirements.txt`
- للتشغيل: `python main.py`

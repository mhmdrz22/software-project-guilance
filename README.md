# Team Task Board – Django + React Starter

این یک پروژه‌ی ساده‌ی Django + React است که به عنوان پروژه‌ی نهایی درس مهندسی نرم‌افزار برای دانشجوها نوشته شده تا روی آن کار کنند و موارد خواسته شده را پیاده‌سازی کنند.

## راه‌اندازی Backend (Django)

```bash
cd backend
python -m venv venv

# Activate virtual environment
venv\Scripts\activate    # Windows
source venv/bin/activate # Linux/macOS

pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 8000
```

## راه‌اندازی Frontend (React + Vite)

در یک ترمینال جدا:

```bash
cd frontend
npm install
npm run dev
```

به‌صورت پیش‌فرض پروژه‌ی فرانت‌اند روی `http://localhost:5173` و پروژه‌ی بک‌اند روی `http://localhost:8000` اجرا می‌شود.

می‌توانید با ساخت یک فایل `.env` داخل پوشه‌ی `frontend` آدرس API را تنظیم کنید:

```env
VITE_API_BASE_URL=http://localhost:8000/api
```

FROM python:3.9-slim

# إعدادات عشان البايثون يبقى سريع وميخزنش كاش
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# تثبيت مكتبات النظام الضرورية لـ PostgreSQL
RUN apt-get update && apt-get install -y \
    libpq-dev gcc \
    && rm -rf /var/lib/apt/lists/*

# نسخ المتطلبات وتثبيتها
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# نسخ باقي المشروع
COPY . .

# فتح البورت
EXPOSE 8501

# أمر التشغيل
CMD ["streamlit", "run", "login.py", "--server.port=8501", "--server.address=0.0.0.0"]
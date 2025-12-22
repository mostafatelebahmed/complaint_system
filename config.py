import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_path = os.path.join(BASE_DIR, "cms.db")
DATABASE_URL = f"sqlite:///{DB_path}"

# Mapping Excel headers (Arabic) to Internal Field names
EXCEL_MAPPING = {
    "رقم الشكوى": "code",
    "موقف الشكوى": "status",
    "الإسم": "customer_name",
    "المشروع": "project_name",
    "التصنيف": "department_name",
    "الشكوى": "description",
    "مصدر الشكوى": "source",
    "تاريخ الرد على الشكوى": "resolution_date",
    "التليفون": "phone",
    "التاريخ": "created_at"
}

# SLA Settings (in days)
SLA_LIMIT_DAYS = 3
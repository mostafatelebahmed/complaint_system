import pandas as pd
from sqlalchemy.orm import Session
from database.models import Complaint, ComplaintHistory, Project, Department
from datetime import datetime, timedelta

class ImportService:
    def process_excel(self, file, db: Session):
        # خريطة الأعمدة (تم إضافة "الرد" و "متابعة الادارة")
        EXCEL_MAPPING = {
            "رقم الشكوى": "code",
            "موقف الشكوى": "status",
            "الإسم": "customer_name",
            "تبعية الشكوى": "project_name",
            "الشكوى": "description",
            "مصدر الشكوى": "source",
            "تاريخ الرد على الشكوى": "resolution_date",
            "الــــــــــــــــرد": "response_text", # الرد الموجود في الإكسل
            "متابعة الادارة": "admin_note",
            "التليفون": "phone",
            "التاريخ": "created_at"
        }

        try:
            if isinstance(file, str):
                df = pd.read_csv(file) if file.endswith('.csv') else pd.read_excel(file)
            else:
                fname = file.name
                df = pd.read_csv(file) if fname.endswith('.csv') else pd.read_excel(file)
            
            df.columns = df.columns.str.strip()
            available_cols = [k for k in EXCEL_MAPPING.keys() if k in df.columns]
            df = df[available_cols].rename(columns=EXCEL_MAPPING)
            
            added_count = 0
            
            for _, row in df.iterrows():
                # 1. المشروع
                proj_name = str(row.get('project_name', 'عام')).strip()
                if proj_name.lower() in ['nan', 'none', '']: proj_name = 'عام'
                
                project = db.query(Project).filter_by(name=proj_name).first()
                if not project:
                    project = Project(name=proj_name)
                    db.add(project)
                    db.commit()
                
                # 2. الإدارة
                dept_name = "وارد عام"
                dept = db.query(Department).filter_by(name=dept_name).first()
                if not dept:
                    dept = Department(name=dept_name)
                    db.add(dept)
                    db.commit()

                # 3. التحقق من التكرار
                code = str(row.get('code', '')).strip()
                if not code or code.lower() in ['nan', ''] or db.query(Complaint).filter_by(code=code).first():
                    continue 

                # 4. التواريخ
                created_at = pd.to_datetime(row.get('created_at'), dayfirst=True, errors='coerce')
                if pd.isna(created_at): created_at = datetime.utcnow()
                
                res_date = pd.to_datetime(row.get('resolution_date'), dayfirst=True, errors='coerce')
                if pd.isna(res_date): res_date = None
                
                # 5. معالجة الحالة بدقة
                raw_status = str(row.get('status', '')).strip()
                final_status = "New"
                
                # منطق الحالات حسب طلبك
                if "تم" in raw_status or res_date is not None:
                    final_status = "Resolved" # تم الحل
                elif "جاري" in raw_status or "استعلام" in raw_status:
                    final_status = "In Progress" # جاري العمل
                
                # 6. حفظ الشكوى
                complaint = Complaint(
                    code=code,
                    customer_name=str(row.get('customer_name', '')),
                    phone=str(row.get('phone', '')),
                    source=str(row.get('source', '')),
                    description=str(row.get('description', '')),
                    status=final_status,
                    created_at=created_at,
                    resolution_date=res_date,
                    project_id=project.id,
                    department_id=dept.id,
                    due_date=created_at + timedelta(days=3)
                )
                db.add(complaint)
                db.commit() # نحفظ أولاً لنحصل على ID
                
                # 7. استيراد الردود القديمة (هام جداً)
                # إذا كان هناك رد في ملف الإكسل، نضيفه كـ "تاريخ"
                old_resp = str(row.get('response_text', ''))
                if old_resp and old_resp.lower() not in ['nan', '', 'nan']:
                    hist = ComplaintHistory(
                        complaint_id=complaint.id,
                        action="رد سابق (أرشيف)",
                        details=old_resp,
                        timestamp=created_at # نستخدم نفس تاريخ الإنشاء تقريباً
                    )
                    db.add(hist)
                
                # إذا كان هناك ملاحظات إدارة
                admin_note = str(row.get('admin_note', ''))
                if admin_note and admin_note.lower() not in ['nan', '', 'nan']:
                     hist_note = ComplaintHistory(
                        complaint_id=complaint.id,
                        action="ملاحظة إدارية",
                        details=admin_note,
                        timestamp=created_at
                    )
                     db.add(hist_note)

                added_count += 1
            
            db.commit()
            return True, f"تم استيراد {added_count} شكوى بنجاح."

        except Exception as e:
            db.rollback()
            return False, f"حدث خطأ: {str(e)}"
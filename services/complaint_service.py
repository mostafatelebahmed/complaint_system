from sqlalchemy.orm import Session, joinedload
from database.models import Complaint, ComplaintHistory, Department, Project
from datetime import datetime, timedelta

class ComplaintService:
    
    # دالة توليد الكود التلقائي
    def generate_next_code(self, db: Session) -> str:
        # نحاول الحصول على آخر شكوى تم إدخالها
        # نستخدم ترتيب عكسي حسب الـ ID
        last_comp = db.query(Complaint).order_by(Complaint.id.desc()).first()
        
        if not last_comp:
            return "1001" # بداية الترقيم
        
        try:
            # محاولة استخراج الرقم من الكود القديم
            # نفترض الكود رقم صحيح مثل 1001
            last_num = int(''.join(filter(str.isdigit, str(last_comp.code))))
            return str(last_num + 1)
        except:
            # لو الكود كان معقد (مثل 2024-A-1) نستخدم ترقيم احتياطي
            return f"{datetime.now().year}-{datetime.now().strftime('%f')[:4]}"

    def create_manual_complaint(self, db: Session, data: dict, sla_days: int):
        # 1. توليد الكود
        auto_code = self.generate_next_code(db)
        
        # 2. تجهيز المشروع والإدارة
        proj_name = data['project']
        project = db.query(Project).filter_by(name=proj_name).first()
        if not project:
            project = Project(name=proj_name)
            db.add(project)
            db.commit()
            
        dept_name = data['department']
        dept = db.query(Department).filter_by(name=dept_name).first()
        if not dept:
            dept = Department(name=dept_name)
            db.add(dept)
            db.commit()
            
        # 3. الحفظ
        new_comp = Complaint(
            code=auto_code,
            customer_name=data['customer_name'],
            phone=data['phone'],
            source=data['source'],
            description=data['description'],
            status="New",
            created_at=data['created_at'],
            project_id=project.id,
            department_id=dept.id,
            due_date=data['created_at'] + timedelta(days=sla_days)
        )
        db.add(new_comp)
        db.commit()
        db.refresh(new_comp)
    
        # === [إضافة الكود ده] تسجيل إشعار للإدارة المختصة ===
        from services.notification_service import NotificationService
        notif_svc = NotificationService()
        msg = f"شكوى جديدة واردة برقم {new_comp.code}"
        notif_svc.add_notification(db, new_comp.department.name, msg, "New", new_comp.id)
        # ===================================================
            
        # 4. السجل
        history = ComplaintHistory(
            complaint_id=new_comp.id,
            action="تسجيل جديد",
            details=f"تم فتح الشكوى آلياً برقم {auto_code}",
            timestamp=datetime.now()
        )
        db.add(history)
        db.commit()
        
        return new_comp # نرجع الكائن بالكامل لعرض بياناته

    def get_all_complaints(self, db: Session, filters=None):
        query = db.query(Complaint).options(
            joinedload(Complaint.project),
            joinedload(Complaint.department),
            joinedload(Complaint.history) # تحميل التاريخ والردود
        )
        
        if filters:
            if filters.get('projects') and "الكل" not in filters['projects']:
                query = query.filter(Complaint.project.has(Project.name.in_(filters['projects'])))
            
            if filters.get('departments') and "الكل" not in filters['departments']:
                query = query.filter(Complaint.department.has(Department.name.in_(filters['departments'])))
            
            if filters.get('status') and filters['status'] != 'All':
                query = query.filter(Complaint.status == filters['status'])
            
            if filters.get('date_range'):
                start_date, end_date = filters['date_range']
                query = query.filter(Complaint.created_at >= start_date, Complaint.created_at <= end_date)
            
            if filters.get('search_text'):
                search = f"%{filters['search_text']}%"
                query = query.filter(
                    (Complaint.customer_name.like(search)) | 
                    (Complaint.code.like(search)) |
                    (Complaint.phone.like(search))
                )
        # ترتيب النتائج الأحدث أولاً
        return query.order_by(Complaint.created_at.desc()).all()

    def get_complaint_by_id(self, db: Session, c_id: int):
        return db.query(Complaint).filter(Complaint.id == c_id).first()

    # 1. دالة إضافة تعليق
    def add_comment(self, db: Session, c_id: int, comment: str, user_id: int = None):
        history = ComplaintHistory(
            complaint_id=c_id,
            action="تعليق / رد",
            details=comment,
            user_id=user_id  # <--- هنا التعديل المهم
        )
        db.add(history)
        db.commit()

    # 2. دالة تحديث الحالة
    def update_status(self, db: Session, c_id: int, new_status: str, user_id: int = None):
        comp = self.get_complaint_by_id(db, c_id)
        if comp:
            old_status = comp.status
            comp.status = new_status
            if new_status == "Resolved" and not comp.resolution_date:
                comp.resolution_date = datetime.utcnow()
            
            history = ComplaintHistory(
                complaint_id=c_id,
                action="تغيير حالة",
                details=f"تغيير من {old_status} إلى {new_status}",
                user_id=user_id # <--- هنا التعديل المهم
            )
            db.add(history)
            db.commit()

    # 3. دالة التحويل
    # --- استبدل دالة التحويل القديمة بهذه الجديدة (لإصلاح زر التحويل) ---
    def transfer_department(self, db, complaint_id, new_dept_name, user_id):
        # 1. نجيب الإدارة الجديدة بالاسم عشان ناخد الـ ID بتاعها
        target_dept = db.query(Department).filter(Department.name == new_dept_name).first()
        
        if target_dept:
            complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()
            if complaint:
                # 2. (مهم جداً) تغيير القسم الحالي للشكوى
                complaint.department_id = target_dept.id 
                complaint.status = "New" # نرجعها جديدة عشان ينتبهوا ليها
                
                # 3. تسجيل في الهيستوري
                history = ComplaintHistory(
                    complaint_id=complaint_id,
                    user_id=user_id,
                    action="إحالة / تحويل",
                    details=f"تم تحويل الشكوى إلى: {new_dept_name}",
                    timestamp=datetime.now()
                )
                db.add(history)
                db.commit()
                return True
        return False
    # --- أضف هذه الدالة الجديدة في نفس الملف (لعمل الإشعارات) ---
    def get_pending_counts(self, db: Session, dept_name: str):
        # هذه الدالة تحسب الشكاوى التي تخص إدارة معينة وليست مغلقة
        # نعتبر أن اسم المستخدم (full_name) هو نفسه اسم الإدارة
        return db.query(Complaint).join(Department).filter(
            Department.name == dept_name,
            Complaint.status.in_(['New', 'In Progress']) # نحسب الجديد والجاري فقط
        ).count()
            
    def delete_all_data(self, db: Session):
        try:
            db.query(ComplaintHistory).delete()
            db.query(Complaint).delete()
            db.query(Project).delete()
            db.query(Department).delete()
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            return False
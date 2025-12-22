from sqlalchemy.orm import Session
from database.models import Notification, Complaint, User
from datetime import datetime, timedelta

class NotificationService:
    
    # 1. إنشاء إشعار جديد
    def add_notification(self, db: Session, dept_name: str, message: str, category: str, related_id: int = None):
        notif = Notification(
            recipient_dept=dept_name,
            message=message,
            category=category,
            related_id=related_id,
            is_read=False,
            created_at=datetime.now()
        )
        db.add(notif)
        db.commit()

    # 2. جلب الإشعارات (المسجلة + اللحظية)
    def get_my_notifications(self, db: Session, user_dept: str, sla_days: int = 3):
        notifications = []
        
        # أ) جلب الإشعارات المسجلة في قاعدة البيانات (تحويلات، جديد)
        db_notifs = db.query(Notification).filter(
            Notification.recipient_dept == user_dept,
            Notification.is_read == False
        ).order_by(Notification.created_at.desc()).all()
        
        for n in db_notifs:
            notifications.append({
                "id": n.id,
                "msg": n.message,
                "type": n.category, # Transfer, New
                "time": n.created_at,
                "link": n.related_id,
                "source": "db"
            })

        # ب) الإشعارات الذكية (تحسب لحظياً)
        
        # 1. تنبيه: شكاوى متأخرة (Overdue)
        overdue_date = datetime.now() - timedelta(days=sla_days)
        
        # نبدأ الاستعلام الأساسي
        q_overdue = db.query(Complaint).filter(
            Complaint.status.in_(['New', 'In Progress']),
            Complaint.created_at < overdue_date
        )
        
        # لو المستخدم مش Admin، نفلتر على إدارته بس
        if user_dept != "Admin":
            q_overdue = q_overdue.filter(Complaint.department.has(name=user_dept))
            
        overdue_count = q_overdue.count()
        
        if overdue_count > 0:
            notifications.append({
                "id": "alert_overdue",
                "msg": f"⚠️ لديك {overdue_count} شكاوى تجاوزت فترة SLA!",
                "type": "Overdue",
                "time": datetime.now(),
                "link": "filter_overdue",
                "source": "system"
            })

        # 2. تنبيه: شكاوى جديدة (New)
        q_new = db.query(Complaint).filter(Complaint.status == 'New')
        
        if user_dept != "Admin":
            q_new = q_new.filter(Complaint.department.has(name=user_dept))
            
        new_count = q_new.count()
        
        if new_count > 0:
             notifications.append({
                "id": "alert_new",
                "msg": f"📥 لديك {new_count} شكاوى جديدة.",
                "type": "New",
                "time": datetime.now(),
                "link": "filter_new",
                "source": "system"
            })

        return notifications

    # 3. قراءة الإشعار (لإخفائه)
    def mark_as_read(self, db: Session, notif_id):
        n = db.query(Notification).filter(Notification.id == notif_id).first()
        if n:
            n.is_read = True
            db.commit()
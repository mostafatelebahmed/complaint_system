from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
# تأكد أن هذا المسار صحيح لديك، أو استخدم declarative_base() مباشرة لو لم يكن لديك ملف connection
from database.connection import Base 

class Project(Base):
    __tablename__ = "projects"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    complaints = relationship("Complaint", back_populates="project")

class Department(Base):
    __tablename__ = "departments"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    complaints = relationship("Complaint", back_populates="department")

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True) # اسم الدخول
    full_name = Column(String) # الاسم الظاهر
    password = Column(String) # كلمة السر
    role = Column(String, default="User") # Admin or User
    
    # العلاقات
    history_logs = relationship("ComplaintHistory", back_populates="user")

class Complaint(Base):
    __tablename__ = "complaints"
    
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, index=True, unique=True)
    
    customer_name = Column(String)
    phone = Column(String, nullable=True)
    source = Column(String, nullable=True)
    description = Column(Text)
    
    status = Column(String, default="New")
    
    created_at = Column(DateTime, default=datetime.utcnow)
    resolution_date = Column(DateTime, nullable=True)
    due_date = Column(DateTime, nullable=True)
    
    project_id = Column(Integer, ForeignKey("projects.id"))
    department_id = Column(Integer, ForeignKey("departments.id"))
    
    project = relationship("Project", back_populates="complaints")
    department = relationship("Department", back_populates="complaints")
    history = relationship("ComplaintHistory", back_populates="complaint", cascade="all, delete-orphan")

class ComplaintHistory(Base):
    __tablename__ = "complaint_history"
    id = Column(Integer, primary_key=True)
    complaint_id = Column(Integer, ForeignKey("complaints.id"))
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True) # ربط المستخدم
    
    action = Column(String) 
    details = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    complaint = relationship("Complaint", back_populates="history")
    user = relationship("User", back_populates="history_logs")

# =========================================================
# ✅ الإضافة الجديدة: جدول الإشعارات
# =========================================================
class Notification(Base):
    __tablename__ = 'notifications'

    id = Column(Integer, primary_key=True, index=True)
    recipient_dept = Column(String) # الإدارة المستهدفة بالإشعار
    message = Column(String)        # نص الإشعار
    category = Column(String)       # نوعه: New, Transfer, Reply, Alert
    related_id = Column(Integer)    # رقم الشكوى المرتبط
    is_read = Column(Boolean, default=False) # هل تم قراءته؟
    created_at = Column(DateTime, default=datetime.utcnow)
import hashlib
from sqlalchemy.orm import Session
from database.models import User

class AuthService:
    def hash_password(self, password):
        return hashlib.sha256(str.encode(password)).hexdigest()

    def create_user(self, db: Session, username, full_name, password, role="User"):
        existing = db.query(User).filter(User.username == username).first()
        if not existing:
            new_user = User(username=username, full_name=full_name, password=self.hash_password(password), role=role)
            db.add(new_user)
            db.commit()
            return True
        return False

    def login(self, db: Session, username, password):
        user = db.query(User).filter(User.username == username).first()
        if user and user.password == self.hash_password(password):
            return user
        return None

    def get_user(self, db: Session, username):
        return db.query(User).filter(User.username == username).first()

    def get_all_users(self, db: Session):
        return db.query(User).all()

    def delete_user(self, db: Session, username):
        user = db.query(User).filter(User.username == username).first()
        if user:
            db.delete(user); db.commit()
            return True
        return False

    def ensure_admin_exists(self, db: Session):
        if not db.query(User).filter(User.role == "Admin").first():
            self.create_user(db, "admin", "مدير النظام", "admin123", "Admin")
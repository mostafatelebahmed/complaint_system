import pandas as pd
from sqlalchemy.orm import Session
from database.models import Complaint

class AnalyticsService:
    def get_kpi_metrics(self, db: Session):
        total = db.query(Complaint).count()
        open_c = db.query(Complaint).filter(Complaint.status.in_(['New', 'In Progress'])).count()
        resolved = db.query(Complaint).filter(Complaint.status == 'Resolved').count()
        
        # Calculate Overdue (Naive implementation)
        # In SQL logic: WHERE status != 'Resolved' AND due_date < NOW
        # Here we do Python side for simplicity with SQLite dates
        df = pd.read_sql(db.query(Complaint.status, Complaint.due_date).statement, db.bind)
        if not df.empty:
            now = pd.Timestamp.now()
            overdue = df[ (df['status'] != 'Resolved') & (df['due_date'] < now) ].shape[0]
        else:
            overdue = 0
            
        return total, open_c, resolved, overdue

    def get_complaints_by_project(self, db: Session):
        query = "SELECT p.name, COUNT(c.id) as count FROM projects p JOIN complaints c ON p.id = c.project_id GROUP BY p.name ORDER BY count DESC LIMIT 10"
        return pd.read_sql(query, db.bind)

    def get_complaints_by_dept(self, db: Session):
        query = "SELECT d.name, COUNT(c.id) as count FROM departments d JOIN complaints c ON d.id = c.department_id GROUP BY d.name"
        return pd.read_sql(query, db.bind)
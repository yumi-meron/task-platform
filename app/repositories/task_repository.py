from sqlalchemy.orm import Session
from uuid import UUID
from typing import List, Optional
from sqlalchemy import desc
from app.models.task import Task, TaskStatus

class TaskRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, task_data: dict) -> Task:
        db_task = Task(**task_data)
        self.db.add(db_task)
        self.db.commit()
        self.db.refresh(db_task)
        return db_task

    def get_by_id(self, task_id: UUID) -> Optional[Task]:
        return self.db.query(Task).filter(Task.id == task_id).first()
    
    def list(self, limit:int, offset:int, status:Optional[TaskStatus] = None) -> List[Task]:
        query = self.db.query(Task)
        if status:
            query = query.filter(Task.status == status)
        return query.order_by(desc(Task.created_at)).offset(offset).limit(limit).all()
    
    def count(self, status: Optional[TaskStatus] = None) -> int:
        query = self.db.query(Task)
        if status:
            query = query.filter(Task.status == status)
        return query.count()
    
from sqlalchemy.orm import Session
from uuid import UUID
from app.repositories.task_repository import TaskRepository
from app.schemas.task import TaskCreate
from app.models.task import TaskStatus

class TaskService:
    def __init__(self, db: Session):
        self.repository = TaskRepository(db)
    
    def create_task(self, task_in :TaskCreate):
        # Business Logic: Prepare data for the repository
        task_data = task_in.model_dump()
        task_data["status"] = TaskStatus.pending
        task_data["retries"] = 0
        return self.repository.create(task_data)
    
    def get_task(self, task_id: UUID):
        return self.repository.get_by_id(task_id)
    
    def get_all_tasks(self, limit: int, offset: int, status: str = None):
        tasks = self.repository.list(limit, offset, status)
        total = self.repository.count(status)
        return tasks, total
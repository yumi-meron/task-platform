from sqlalchemy.orm import Session
from uuid import UUID
from app.repositories.task_repository import TaskRepository
from app.schemas.task import TaskCreate
from app.models.task import TaskStatus


class TaskService:
    def __init__(self, db: Session):
        self.repository = TaskRepository(db)
        self.db = db
    
    def create_task(self, task_in :TaskCreate):
        from app.worker.tasks import process_task # Its imported locally not to cause a circular import with worker.tasks
        # Business Logic: Prepare data for the repository
        task_data = task_in.model_dump()
        task_data["status"] = TaskStatus.pending
        task_data["retries"] = 0

        new_task =self.repository.create(task_data)

        # Trigger Celery (Notice we use .delay())
        # .delay() sends the task_id to Redis and returns immediately
        process_task.delay(str(new_task.id))

        return new_task
    
    def get_task(self, task_id: UUID):
        return self.repository.get_by_id(task_id)
    
    def get_all_tasks(self, limit: int, offset: int, status: str = None):
        tasks = self.repository.list(limit, offset, status)
        total = self.repository.count(status)
        return tasks, total
    
    def manual_retry(self, task_id: UUID):
        from app.worker.tasks import process_task

        task = self.repository.get_by_id(task_id)
        if not task: 
            return None
        if task.status != TaskStatus.failed:
            return task
        
        # Logic to reset and re-enqueue
        task.status = TaskStatus.pending
        task.retries = 0
        self.db.commit()

        process_task.delay(str(task.id))
        return task

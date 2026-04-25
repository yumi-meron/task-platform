from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from uuid import UUID

from app.models.task import TaskStatus
from app.services.task_service import TaskService
from app.schemas.task import TaskCreate, TaskListResponse, TaskResponse
from app.db.deps import get_db
from app.worker.tasks import process_task

router = APIRouter(prefix="/tasks", tags=["tasks"])

# POST /tasks - Create a task
@router.post("/", response_model=TaskResponse, status_code=201)
def create_task(task_in: TaskCreate, db: Session = Depends(get_db)):
    service = TaskService(db)
    return service.create_task(task_in)

# GET /tasks/{id} - Get specific task
@router.get("/{task_id}", response_model=TaskResponse)
def get_task(task_id: UUID, db: Session = Depends(get_db)):
    service = TaskService(db)
    task = service.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

# GET /tasks - List with pagination, sorting, and filtering
@router.get("/", response_model= TaskListResponse)
def list_tasks(
    db: Session = Depends(get_db),
    limit: int = Query(10, ge=1),
    offset: int = Query(0, ge = 0),
    status: str = None 
): 
    service = TaskService(db)
    tasks, total = service.get_all_tasks(limit, offset, status)
    return {"tasks" : tasks, "total" : total}

@router.post("/{task_id}/retry", response_model=TaskResponse)
def retry_task(task_id : UUID, db: Session = Depends(get_db)):
    service = TaskService(db)
    task = service.manual_retry(task_id)

    if not task:
        raise HTTPException(status_code=404, detail = "Task not found")

    if task.status != TaskStatus.failed:
        raise HTTPException(
            status_code=400,
            detail= f"Only failed tasks can be retried. Current status: {task.status}"
        )

    return task
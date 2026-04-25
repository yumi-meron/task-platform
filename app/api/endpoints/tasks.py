from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from uuid import UUID
from typing import List, Optional

from app.models.task import Task, TaskStatus
from app.schemas.task import TaskCreate, TaskListResponse, TaskResponse
from app.db.deps import get_db

router = APIRouter(prefix="/tasks", tags=["tasks"])

# POST /tasks - Create a task
@router.post("/", response_model=TaskResponse, status_code=201)
def create_task(task_in: TaskCreate, db: Session = Depends(get_db)):
    new_task = Task(
        payload = task_in.payload,
        priority = task_in.priority,
        status = TaskStatus.pending, # Force initial status
        retries = 0
    )
    db.add(new_task)
    db.commit()
    db.refresh(new_task)
    return new_task

# GET /tasks/{id} - Get specific task
@router.get("/{task_id}", response_model=TaskResponse)
def get_task(task_id: UUID, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

# GET /tasks - List with pagination, sorting, and filtering
@router.get("/", response_model= TaskListResponse)
def list_tasks(
    db: Session = Depends(get_db),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge = 0),
    status: Optional[TaskStatus] = None # Stretch goal: Filtering
):
    query = db.query(Task)

    # Apply filtering (Stretch Goal)
    if status:
        query = query.filter(Task.status == status)

    # Apply sorting
    query = query.order_by(desc(Task.created_at))

    total = query.count()
    tasks = query.offset(offset).limit(limit).all()

    return {"tasks" : tasks, "total" : total}



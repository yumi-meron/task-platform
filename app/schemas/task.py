from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID
from typing import Any,Dict,List, Optional
from app.models.task import TaskStatus

# What the user sends to create a task
class TaskCreate(BaseModel):
    payload: Dict[str, Any]
    priority: int = 0

# What the API returns for a single task
class TaskResponse(BaseModel):
    id: UUID
    status: TaskStatus
    payload: Dict[str,Any]
    priority: int
    retries: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True # This tells Pydantic to read data from SQLAlchemy objects

# What the API returns for a list of tasks
class TaskListResponse(BaseModel):
    tasks: List[TaskResponse]
    total: int
     
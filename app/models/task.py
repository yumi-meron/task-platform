import uuid, enum
from datetime import datetime
from typing import Any, Dict

from sqlalchemy import Enum, JSON, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base

# 1. Status Enum
class TaskStatus(str, enum.Enum):
    pending = "pending"
    processing = "processing"
    completed = "completed"
    failed = "failed"

# 2. Task Model (sqlalchemy 2.0 style)
class Task(Base):
    __tablename__ = "tasks"

    # Mapped[type] defines the Python type
    # mapped_column() defines the Database constraints
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    status: Mapped[TaskStatus] = mapped_column(
        Enum(TaskStatus),
        nullable=False,
        default=TaskStatus.pending,
        index=True
    )

    # Use Dict[str, Any] so Python knows payload is a dictionary
    payload: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)

    priority: Mapped[int] = mapped_column(default=0, index=True)

    retries: Mapped[int] = mapped_column(default=0)

    # func.now() handles the timestamp on the database server side
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )
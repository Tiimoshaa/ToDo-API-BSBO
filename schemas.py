# schemas.py
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    is_important: bool
    is_urgent: bool
    deadline_at: Optional[datetime] = None

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    is_important: Optional[bool] = None
    is_urgent: Optional[bool] = None
    deadline_at: Optional[datetime] = None
    completed: Optional[bool] = None

class TaskResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    is_important: bool
    is_urgent: bool
    quadrant: str

    deadline_at: Optional[datetime]
    completed: bool
    created_at: datetime
    completed_at: Optional[datetime] = None

    days_left: Optional[int]
    is_overdue: bool

    class Config:
        from_attributes = True

class TimingStatsResponse(BaseModel):
    completed_on_time: int = Field(
        ...,
        description="Количество задач, завершенных в срок"
    )
    completed_late: int = Field(
        ...,
        description="Количество задач, завершенных с нарушением сроков"
    )
    on_plan_pending: int = Field(
        ...,
        description="Количество задач в работе, выполняемых в соответствии с планом"
    )
    overtime_pending: int = Field(
        ...,
        description="Количество просроченных незавершенных задач"
    )


from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

# Базовая схема для Task.
# Все поля, которые есть в нашей "базе данных" tasks_db
class TaskBase(BaseModel):
    title: str = Field(..., min_length=3, max_length=100, description="Название задачи")
    description: Optional[str] = Field(None, max_length=500, description="Описание задачи")
    is_important: bool = Field(..., description="Важность задачи")
    # is_urgent убираем из TaskCreate; будет вычисляться на сервере
    # is_urgent: bool = Field(...)
class TaskCreate(TaskBase):
    deadline_at: Optional[datetime] = Field(None, description="Дедлайн задачи (UTC)")
    pass

# Схема для обновления задачи (используется в PUT)
# Все поля опциональные, т.к. мы можем захотеть обновить только title или status
class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=3, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    is_important: Optional[bool] = None
    # is_urgent optional if admin wants to override, but per methodic - server calculates it
    deadline_at: Optional[datetime] = None
    completed: Optional[bool] = None

class TaskResponse(TaskBase):
    id: int
    quadrant: str
    completed: bool = False
    created_at: datetime
    completed_at: Optional[datetime] = None
    deadline_at: Optional[datetime] = None  # from DB
    days_until_deadline: Optional[int] = None  # computed
    is_overdue: Optional[bool] = None  # computed

    class Config:
        from_attributes = True

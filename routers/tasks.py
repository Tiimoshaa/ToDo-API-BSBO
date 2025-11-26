# routers/tasks.py
from fastapi import APIRouter, HTTPException, Depends, status, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, and_
from datetime import datetime, timezone

from database import get_async_session
from models import Task
from schemas import TaskResponse, TaskCreate, TaskUpdate
from utils import calculate_urgency, calculate_days_until_deadline, determine_quadrant

router = APIRouter(
    prefix="/tasks",
    tags=["tasks"],
)

# helper: build response dict including computed deadline info
def build_task_response(task: Task) -> dict:
    days = calculate_days_until_deadline(task.deadline_at)
    is_overdue = None
    if days is not None:
        is_overdue = days < 0
    # Map fields manually to avoid _sa_instance_state leaking
    return {
        "id": task.id,
        "title": task.title,
        "description": task.description,
        "is_important": task.is_important,
        "is_urgent": task.is_urgent,
        "quadrant": task.quadrant,
        "completed": task.completed,
        "created_at": task.created_at,
        "completed_at": task.completed_at,
        "deadline_at": task.deadline_at,
        "days_until_deadline": days,
        "is_overdue": is_overdue,
    }

# GET all tasks
@router.get("/", response_model=list[TaskResponse])
async def get_all_tasks(db: AsyncSession = Depends(get_async_session)):
    result = await db.execute(select(Task))
    tasks = result.scalars().all()
    return [build_task_response(t) for t in tasks]


# GET quadrant
@router.get("/quadrant/{quadrant}", response_model=list[TaskResponse])
async def get_tasks_by_quadrant(quadrant: str, db: AsyncSession = Depends(get_async_session)):
    if quadrant not in ["Q1", "Q2", "Q3", "Q4"]:
        raise HTTPException(status_code=400, detail="Неверный квадрант. Используйте: Q1, Q2, Q3, Q4")
    result = await db.execute(select(Task).where(Task.quadrant == quadrant))
    tasks = result.scalars().all()
    return [build_task_response(t) for t in tasks]

# GET status
@router.get("/status/{status}", response_model=list[TaskResponse])
async def get_tasks_by_status(status: str, db: AsyncSession = Depends(get_async_session)):
    if status not in ["completed", "pending"]:
        raise HTTPException(status_code=400, detail="Статус должен быть: completed или pending")
    is_completed = (status == "completed")
    result = await db.execute(select(Task).where(Task.completed == is_completed))
    tasks = result.scalars().all()
    return [build_task_response(t) for t in tasks]

# GET search
@router.get("/search", response_model=list[TaskResponse])
async def search_tasks(q: str = Query(..., min_length=2), db: AsyncSession = Depends(get_async_session)):
    q_pattern = f"%{q}%"
    result = await db.execute(
        select(Task).where(
            or_(
                Task.title.ilike(q_pattern),
                Task.description.ilike(q_pattern)
            )
        )
    )
    tasks = result.scalars().all()
    return [build_task_response(t) for t in tasks]

# POST create task (user provides deadline_at instead of is_urgent)
@router.post("/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(task_data: TaskCreate, db: AsyncSession = Depends(get_async_session)):
    # calculate urgency based on deadline
    new_is_urgent = calculate_urgency(task_data.deadline_at)
    # quadrant by importance and computed urgency
    quadrant = determine_quadrant(task_data.is_important, new_is_urgent)

    new_task = Task(
        title=task_data.title,
        description=task_data.description,
        is_important=task_data.is_important,
        is_urgent=new_is_urgent,
        quadrant=quadrant,
        completed=False,
        created_at=datetime.now(timezone.utc),
        deadline_at=task_data.deadline_at
    )

    db.add(new_task)
    await db.commit()
    await db.refresh(new_task)

    return build_task_response(new_task)

# GET task by id
@router.get("/{task_id}", response_model=TaskResponse)
async def get_task_by_id(task_id: int, db: AsyncSession = Depends(get_async_session)):
    task = await db.scalar(select(Task).where(Task.id == task_id))
    if not task:
        raise HTTPException(status_code=404, detail="Задача не найдена")
    return build_task_response(task)

# PUT update
@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(task_id: int, update_data: TaskUpdate, db: AsyncSession = Depends(get_async_session)):
    task = await db.scalar(select(Task).where(Task.id == task_id))
    if not task:
        raise HTTPException(status_code=404, detail="Задача не найдена")

    update_fields = update_data.model_dump(exclude_unset=True)
    for field, value in update_fields.items():
        setattr(task, field, value)

    # if deadline changed or importance changed -> recalc urgency and quadrant
    if "deadline_at" in update_fields or "is_important" in update_fields:
        new_urgency = calculate_urgency(task.deadline_at)
        task.is_urgent = new_urgency
        task.quadrant = determine_quadrant(task.is_important, task.is_urgent)

    await db.commit()
    await db.refresh(task)
    return build_task_response(task)

# PATCH complete
@router.patch("/{task_id}/complete", response_model=TaskResponse)
async def complete_task(task_id: int, db: AsyncSession = Depends(get_async_session)):
    task = await db.scalar(select(Task).where(Task.id == task_id))
    if not task:
        raise HTTPException(status_code=404, detail="Задача не найдена")
    task.completed = True
    task.completed_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(task)
    return build_task_response(task)

# DELETE
@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(task_id: int, db: AsyncSession = Depends(get_async_session)):
    task = await db.scalar(select(Task).where(Task.id == task_id))
    if not task:
        raise HTTPException(status_code=404, detail="Задача не найдена")
    await db.delete(task)
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)

# NEW: tasks that expire today (UTC)
@router.get("/today", response_model=list[TaskResponse])
async def tasks_due_today(db: AsyncSession = Depends(get_async_session)):
    now = datetime.now(timezone.utc)
    # start of today UTC and start of tomorrow UTC
    start = datetime(now.year, now.month, now.day, tzinfo=timezone.utc)
    end = start.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
    result = await db.execute(select(Task).where(Task.deadline_at >= start, Task.deadline_at < end))
    tasks = result.scalars().all()
    return [build_task_response(t) for t in tasks]

# NEW: endpoint returning deadline info only
@router.get("/{task_id}/deadline")
async def get_task_deadline(task_id: int, db: AsyncSession = Depends(get_async_session)):
    task = await db.scalar(select(Task).where(Task.id == task_id))
    if not task:
        raise HTTPException(status_code=404, detail="Задача не найдена")
    days = calculate_days_until_deadline(task.deadline_at)
    is_overdue = None if days is None else (days < 0)
    return {
        "task_id": task.id,
        "deadline_at": task.deadline_at,
        "days_left": days,
        "is_overdue": is_overdue
    }

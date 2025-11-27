# routers/tasks.py
from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_

from datetime import datetime

from database import get_async_session
from models import Task
from schemas import TaskResponse, TaskCreate, TaskUpdate
from utils import calculate_days_until_deadline, calculate_urgency, determine_quadrant

router = APIRouter(
    prefix="/tasks",
    tags=["tasks"]
)


@router.get("/", response_model=list[TaskResponse])
async def get_all_tasks(db: AsyncSession = Depends(get_async_session)):
    result = await db.execute(select(Task))
    tasks = result.scalars().all()

    for t in tasks:
        t.days_left = t.days_left()
        t.is_overdue = t.is_overdue()

    return tasks




@router.get("/search", response_model=list[TaskResponse])
async def search_tasks(q: str, db: AsyncSession = Depends(get_async_session)):
    if len(q) < 2:
        raise HTTPException(400, "Минимальная длина строки — 2 символа")

    result = await db.execute(
        select(Task).where(
            or_(
                Task.title.ilike(f"%{q}%"),
                Task.description.ilike(f"%{q}%")
            )
        )
    )

    tasks = result.scalars().all()

    for t in tasks:
        t.days_left = t.days_left()
        t.is_overdue = t.is_overdue()

    return tasks

@router.get("/{task_id}", response_model=TaskResponse)
async def get_task_by_id(task_id: int, db: AsyncSession = Depends(get_async_session)):
    task = await db.scalar(select(Task).where(Task.id == task_id))

    if not task:
        raise HTTPException(404, "Задача не найдена")

    task.days_left = task.days_left()
    task.is_overdue = task.is_overdue()

    return task

@router.post("/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(data: TaskCreate, db: AsyncSession = Depends(get_async_session)):

    days_left = calculate_days_until_deadline(data.deadline_at)
    is_urgent = calculate_urgency(days_left)
    quadrant = determine_quadrant(data.is_important, is_urgent)

    new_task = Task(
        title=data.title,
        description=data.description,
        is_important=data.is_important,
        is_urgent=is_urgent,
        quadrant=quadrant,
        deadline_at=data.deadline_at,
        completed=False,
        created_at=datetime.utcnow()
    )

    db.add(new_task)
    await db.commit()
    await db.refresh(new_task)

    new_task.days_left = new_task.days_left()
    new_task.is_overdue = new_task.is_overdue()

    return new_task


@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(task_id: int, data: TaskUpdate, db: AsyncSession = Depends(get_async_session)):

    task = await db.scalar(select(Task).where(Task.id == task_id))
    if not task:
        raise HTTPException(404, "Задача не найдена")

    update_fields = data.model_dump(exclude_unset=True)

    for key, value in update_fields.items():
        setattr(task, key, value)

    if "deadline_at" in update_fields or "is_important" in update_fields:
        days_left = calculate_days_until_deadline(task.deadline_at)
        task.is_urgent = calculate_urgency(days_left)
        task.quadrant = determine_quadrant(task.is_important, task.is_urgent)

    await db.commit()
    await db.refresh(task)

    task.days_left = task.days_left()
    task.is_overdue = task.is_overdue()

    return task


@router.patch("/{task_id}/complete", response_model=TaskResponse)
async def complete_task(task_id: int, db: AsyncSession = Depends(get_async_session)):

    task = await db.scalar(select(Task).where(Task.id == task_id))
    if not task:
        raise HTTPException(404, "Задача не найдена")

    task.completed = True
    task.completed_at = datetime.utcnow()

    await db.commit()
    await db.refresh(task)

    task.days_left = task.days_left()
    task.is_overdue = task.is_overdue()

    return task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(task_id: int, db: AsyncSession = Depends(get_async_session)):

    task = await db.scalar(select(Task).where(Task.id == task_id))
    if not task:
        raise HTTPException(404, "Задача не найдена")

    await db.delete(task)
    await db.commit()

    return {}

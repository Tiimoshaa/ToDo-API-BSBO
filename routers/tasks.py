from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, func
from datetime import datetime, date

from database import get_async_session
from models import Task, User, UserRole
from schemas import TaskResponse, TaskCreate, TaskUpdate
from utils import calculate_days_until_deadline, calculate_urgency, determine_quadrant
from dependencies import get_current_user

router = APIRouter(
    prefix="/tasks",
    tags=["tasks"]
)


def enrich(task: Task) -> TaskResponse:
    item = TaskResponse.from_orm(task)

    item.days_left = calculate_days_until_deadline(task.deadline_at)
    item.is_overdue = item.days_left is not None and item.days_left < 0

    return item



@router.get("/", response_model=list[TaskResponse])
async def get_all_tasks(
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    if current_user.role == UserRole.ADMIN:
        result = await db.execute(select(Task))
    else:
        result = await db.execute(
            select(Task).where(Task.user_id == current_user.id)
        )

    tasks = result.scalars().all()
    return [enrich(t) for t in tasks]



@router.get("/search", response_model=list[TaskResponse])
async def search_tasks(
    q: str,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    if len(q) < 2:
        raise HTTPException(400, "Минимальная длина строки — 2 символа")

    stmt = select(Task).where(
        or_(
            Task.title.ilike(f"%{q}%"),
            Task.description.ilike(f"%{q}%")
        )
    )

    if current_user.role != UserRole.ADMIN:
        stmt = stmt.where(Task.user_id == current_user.id)

    result = await db.execute(stmt)
    tasks = result.scalars().all()

    return [enrich(t) for t in tasks]



@router.get("/today", response_model=list[TaskResponse])
async def get_tasks_due_today(
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    today = date.today()

    stmt = select(Task).where(
        func.date(Task.deadline_at) == today,
        Task.deadline_at.is_not(None)
    )

    if current_user.role != UserRole.ADMIN:
        stmt = stmt.where(Task.user_id == current_user.id)

    result = await db.execute(stmt)
    tasks = result.scalars().all()

    return [enrich(t) for t in tasks]



@router.get("/{task_id}", response_model=TaskResponse)
async def get_task_by_id(
    task_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    stmt = select(Task).where(Task.id == task_id)

    if current_user.role != UserRole.ADMIN:
        stmt = stmt.where(Task.user_id == current_user.id)

    task = await db.scalar(stmt)

    if not task:
        raise HTTPException(404, "Задача не найдена")

    return enrich(task)



@router.post("/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    data: TaskCreate,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
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
        created_at=datetime.utcnow(),
        user_id=current_user.id  # ← ключевая строка
    )

    db.add(new_task)
    await db.commit()
    await db.refresh(new_task)

    return enrich(new_task)



@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: int,
    data: TaskUpdate,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    stmt = select(Task).where(Task.id == task_id)

    if current_user.role != UserRole.ADMIN:
        stmt = stmt.where(Task.user_id == current_user.id)

    task = await db.scalar(stmt)

    if not task:
        raise HTTPException(404, "Задача не найдена или нет доступа")

    update_fields = data.model_dump(exclude_unset=True)

    for key, value in update_fields.items():
        setattr(task, key, value)

    if "deadline_at" in update_fields or "is_important" in update_fields:
        days_left = calculate_days_until_deadline(task.deadline_at)
        task.is_urgent = calculate_urgency(days_left)
        task.quadrant = determine_quadrant(task.is_important, task.is_urgent)

    await db.commit()
    await db.refresh(task)

    return enrich(task)



@router.patch("/{task_id}/complete", response_model=TaskResponse)
async def complete_task(
    task_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    stmt = select(Task).where(Task.id == task_id)

    if current_user.role != UserRole.ADMIN:
        stmt = stmt.where(Task.user_id == current_user.id)

    task = await db.scalar(stmt)

    if not task:
        raise HTTPException(404, "Задача не найдена или нет доступа")

    task.completed = True
    task.completed_at = datetime.utcnow()

    await db.commit()
    await db.refresh(task)

    return enrich(task)



@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    stmt = select(Task).where(Task.id == task_id)

    if current_user.role != UserRole.ADMIN:
        stmt = stmt.where(Task.user_id == current_user.id)

    task = await db.scalar(stmt)

    if not task:
        raise HTTPException(404, "Задача не найдена или нет доступа")

    await db.delete(task)
    await db.commit()

    return {}

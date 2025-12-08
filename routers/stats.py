from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, case
from datetime import datetime, timezone

from models import Task, User, UserRole
from database import get_async_session
from schemas import TimingStatsResponse
from dependencies import get_current_user

router = APIRouter(
    prefix="/stats",
    tags=["statistics"]
)



@router.get("/", response_model=dict)
async def get_tasks_stats(
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
) -> dict:

    stmt = select(Task)

    if current_user.role != UserRole.ADMIN:
        stmt = stmt.where(Task.user_id == current_user.id)

    result = await db.execute(stmt)
    tasks = result.scalars().all()

    total_tasks = len(tasks)

    by_quadrant = {"Q1": 0, "Q2": 0, "Q3": 0, "Q4": 0}
    by_status = {"completed": 0, "pending": 0}

    for t in tasks:
        by_quadrant[t.quadrant] = by_quadrant.get(t.quadrant, 0) + 1
        if t.completed:
            by_status["completed"] += 1
        else:
            by_status["pending"] += 1

    return {
        "total_tasks": total_tasks,
        "by_quadrant": by_quadrant,
        "by_status": by_status
    }


@router.get("/timing", response_model=TimingStatsResponse)
async def get_deadline_stats(
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
) -> TimingStatsResponse:

    now_utc = datetime.now(timezone.utc)

    stmt = select(
        func.sum(
            case(((Task.completed == True) & (Task.completed_at <= Task.deadline_at), 1), else_=0)
        ).label("completed_on_time"),
        func.sum(
            case(((Task.completed == True) & (Task.completed_at > Task.deadline_at), 1), else_=0)
        ).label("completed_late"),
        func.sum(
            case(((Task.completed == False) & (Task.deadline_at != None) & (Task.deadline_at > now_utc), 1), else_=0)
        ).label("on_plan_pending"),
        func.sum(
            case(((Task.completed == False) & (Task.deadline_at != None) & (Task.deadline_at <= now_utc), 1), else_=0)
        ).label("overdue_pending"),
    ).select_from(Task)

    if current_user.role != UserRole.ADMIN:
        stmt = stmt.where(Task.user_id == current_user.id)

    result = await db.execute(stmt)
    stats_row = result.one()

    return TimingStatsResponse(
        completed_on_time=stats_row.completed_on_time or 0,
        completed_late=stats_row.completed_late or 0,
        on_plan_pending=stats_row.on_plan_pending or 0,
        overtime_pending=stats_row.overdue_pending or 0,
    )

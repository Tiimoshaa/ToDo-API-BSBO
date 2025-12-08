# routers/admin.py
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from database import get_async_session
from models import User, Task
from dependencies import get_current_admin
from schemas_auth import UserWithTasksCount
from typing import List

router = APIRouter(
    prefix="/admin",
    tags=["admin"]
)


@router.get("/users", response_model=List[UserWithTasksCount])
async def get_all_users_with_task_counts(
    db: AsyncSession = Depends(get_async_session),
    admin_user=Depends(get_current_admin) 
):
    stmt = (
        select(
            User.id,
            User.nickname,
            User.email,
            User.role,
            func.coalesce(func.count(Task.id), 0).label("tasks_count")
        )
        .select_from(User)
        .outerjoin(Task, Task.user_id == User.id)
        .group_by(User.id)
    )

    result = await db.execute(stmt)
    rows = result.all()

    users = [
        {
            "id": row.id,
            "nickname": row.nickname,
            "email": row.email,
            "role": row.role.value, 
            "tasks_count": row.tasks_count
        }
        for row in rows
    ]

    return users

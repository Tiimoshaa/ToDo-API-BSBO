from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from datetime import datetime


router = APIRouter(
    prefix = "/tasks",
    tags = ["tasks"],
    responses = {404: {"description": "Task not found"}}
)



# Временное хранилище (позже будет заменено на PostgreSQL)
tasks_db: List[Dict[str, Any]] = [
    {
        "id": 1,
        "title": "Сдать проект по FastAPI",
        "description": "Завершить разработку API и написать документацию",
        "is_important": True,
        "is_urgent": True,
        "quadrant": "Q1",
        "completed": False,
        "created_at": datetime.now()
    },
    {
        "id": 2,
        "title": "Изучить SQLAlchemy",
        "description": "Прочитать документацию и попробовать примеры",
        "is_important": True,
        "is_urgent": False,
        "quadrant": "Q2",
        "completed": False,
        "created_at": datetime.now()
    },
    {
        "id": 3,
        "title": "Сходить на лекцию",
        "description": None,
        "is_important": False,
        "is_urgent": True,
        "quadrant": "Q3",
        "completed": False,
        "created_at": datetime.now()
    },
    {
        "id": 4,
        "title": "Посмотреть сериал",
        "description": "Новый сезон любимого сериала",
        "is_important": False,
        "is_urgent": False,
        "quadrant": "Q4",
        "completed": True,
        "created_at": datetime.now()
    },
]





@router.get("")
async def get_all_tasks() -> dict:
    return {
        "count": len(tasks_db), 
        "tasks": tasks_db
    }
@router.get("/quadrant/{quadrant}")
async def get_tasks_by_quadrant(quadrant: str) -> dict:
    if quadrant not in ["Q1", "Q2", "Q3", "Q4"]:
        raise HTTPException( #специальный класс в FastAPI для возврата HTTP ошибок.Не забудьте добавть его вызов в 1 строке
            status_code=400,
            detail="Неверный квадрант. Используйте: Q1, Q2, Q3, Q4" #текст, который будетвыведен пользователю
        )
    filtered_tasks = [
        task # ЧТО добавляем в список
        for task in tasks_db # ОТКУДА берем элементы
        if task["quadrant"] == quadrant # УСЛОВИЕ фильтрации
    ]
    return {
        "quadrant": quadrant,
        "count": len(filtered_tasks),
        "tasks": filtered_tasks
    }



# 2
@router.get("/stats")
async def get_tasks_stats() -> dict:
    total = len(tasks_db)

    by_quadrant = {
        "Q1": len([t for t in tasks_db if t["quadrant"] == "Q1"]),
        "Q2": len([t for t in tasks_db if t["quadrant"] == "Q2"]),
        "Q3": len([t for t in tasks_db if t["quadrant"] == "Q3"]),
        "Q4": len([t for t in tasks_db if t["quadrant"] == "Q4"]),
    }

    by_status = {
        "completed": len([t for t in tasks_db if t["completed"] is True]),
        "pending": len([t for t in tasks_db if t["completed"] is False]),
    }

    return {
        "total_tasks": total,
        "by_quadrant": by_quadrant,
        "by_status": by_status
    }

# 3
@router.get("/status/{status}")
async def get_tasks_by_status(status: str) -> dict:
    if status not in ["completed", "pending"]:
        raise HTTPException(
            status_code=404,
            detail="Статус должен быть: completed или pending"
        )
    
    is_completed = True if status == "completed" else False

    filtered = [t for t in tasks_db if t["completed"] == is_completed]

    return {
        "status": status,
        "count": len(filtered),
        "tasks": filtered
    }


# 4
@router.get("/search")
async def search_tasks(q: str) -> dict:
    if len(q) < 2:
        raise HTTPException(
            status_code=400,
            detail="Поисковый запрос должен содержать минимум 2 символа"
        )

    q_lower = q.lower()

    results = [
        task for task in tasks_db
        if q_lower in task["title"].lower()
        or (task["description"] and q_lower in task["description"].lower())
    ]

    return {
        "query": q,
        "count": len(results),
        "tasks": results
    }


# 1
@router.get("/{task_id}")
async def get_task_by_id(task_id: int) -> dict:
    task = next((t for t in tasks_db if t["id"] == task_id), None)
    
    if not task:
        raise HTTPException(
            status_code=404,
            detail=f"Задача с ID {task_id} не найдена"
        )

    return task
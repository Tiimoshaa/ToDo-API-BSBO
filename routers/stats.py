from fastapi import APIRouter
from database import tasks_db

router = APIRouter(
    prefix="/stats",
    tags=["stats"]
)

@router.get("/")
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

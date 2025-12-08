from fastapi import FastAPI, Depends
from contextlib import asynccontextmanager
from database import init_db, get_async_session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from routers import tasks, stats, auth
from scheduler import start_scheduler

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Запуск приложения...")
    print("Инициализация базы данных...")

    await init_db()

    print("База инициализирована!")

    # 🔥 Запускаем планировщик ПЕРЕД yield
    scheduler = start_scheduler()
    print("Планировщик запущен!")

    # --- точка входа приложения ---
    yield

    # --- код закрытия ---
    print("Остановка приложения...")
    scheduler.shutdown()
    print("Планировщик остановлен. Приложение завершено.")
    

app = FastAPI(
    title="ToDo лист API",
    description="API для управления задачами по Матрице Эйзенхауэра",
    version="2.1.0",
    contact={"name": "Тимофей"},
    lifespan=lifespan
)

app.include_router(auth.router, prefix="/api/v3")
app.include_router(tasks.router, prefix="/api/v3")
app.include_router(stats.router, prefix="/api/v3")


@app.get("/")
async def read_root() -> dict:
    return {
        "message": "Task Manager API - Управление задачами по матрице Эйзенхауэра",
        "version": "3.0.0",
        "database": "PostgreSQL (Supabase)",
        "docs": "/docs",
        "redoc": "/redoc",
    }

@app.get("/health")
async def health_check(
    db: AsyncSession = Depends(get_async_session)
) -> dict:
    """
    Проверка здоровья API и динамическая проверка подключения к БД.
    """
    try:
        # Пытаемся выполнить простейший запрос к БД
        await db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception:
        db_status = "disconnected"
    return {
        "status": "healthy",
        "database": db_status
    }

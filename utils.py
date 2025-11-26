# utils.py
from datetime import datetime, timezone
from typing import Optional

def calculate_urgency(deadline_at: Optional[datetime]) -> bool:
    """
    Возвращает True, если до дедлайна 3 дня или меньше (включительно).
    Если deadline_at is None -> False.
    Работает с aware и naive datetime (если naive, предполагает UTC).
    """
    if deadline_at is None:
        return False

    now = datetime.now(timezone.utc)

    # если передан naive datetime — считаем его за UTC
    if deadline_at.tzinfo is None:
        deadline_at = deadline_at.replace(tzinfo=timezone.utc)

    delta = deadline_at - now
    # delta.days округляет вниз; если менее 0 — просрочено
    return delta.days <= 3

def calculate_days_until_deadline(deadline_at: Optional[datetime]) -> Optional[int]:
    """
    Возвращает целое количество дней до дедлайна (может быть отрицательным),
    или None, если дедлайна нет.
    """
    if deadline_at is None:
        return None

    now = datetime.now(timezone.utc)
    if deadline_at.tzinfo is None:
        deadline_at = deadline_at.replace(tzinfo=timezone.utc)

    delta = deadline_at - now
    return delta.days

def determine_quadrant(is_important: bool, is_urgent: bool) -> str:
    """
    Возвращает квадрант матрицы Эйзенхауэра: Q1..Q4
    """
    if is_important and is_urgent:
        return "Q1"
    if is_important and not is_urgent:
        return "Q2"
    if not is_important and is_urgent:
        return "Q3"
    return "Q4"

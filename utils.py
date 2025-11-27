# utils.py
from datetime import datetime
from typing import Optional


def calculate_days_until_deadline(deadline_at: Optional[datetime]) -> Optional[int]:
    """Возвращает количество дней до дедлайна или None"""
    if not deadline_at:
        return None
    return (deadline_at.date() - datetime.utcnow().date()).days


def calculate_urgency(days_left: Optional[int]) -> bool:
    """Возвращает True, если до дедлайна <= 3 дней"""
    if days_left is None:
        return False
    return days_left <= 3


def determine_quadrant(is_important: bool, is_urgent: bool) -> str:
    """Определяет квадрант Эйзенхауэра"""
    if is_important and is_urgent:
        return "Q1"
    if is_important and not is_urgent:
        return "Q2"
    if not is_important and is_urgent:
        return "Q3"
    return "Q4"

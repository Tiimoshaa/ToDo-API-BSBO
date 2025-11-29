from datetime import datetime, timezone

def calculate_days_until_deadline(deadline_at):
    if deadline_at is None:
        return None
    
    # Приводим к aware-datetime
    if deadline_at.tzinfo is None:
        deadline_at = deadline_at.replace(tzinfo=timezone.utc)

    now = datetime.now(timezone.utc)
    diff = (deadline_at - now).days
    return diff

def calculate_urgency(deadline_at):
    days_left = calculate_days_until_deadline(deadline_at)

    if days_left is None:
        return False  # нет дедлайна = не срочно

    return days_left <= 2  # срок до 2 дней = срочно

def determine_quadrant(is_important, is_urgent):
    if is_important and is_urgent:
        return "Q1"
    if is_important and not is_urgent:
        return "Q2"
    if not is_important and is_urgent:
        return "Q3"
    return "Q4"

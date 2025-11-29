from sqlalchemy.ext.hybrid import hybrid_property
from datetime import datetime

class Task(Base):
    ...

    @hybrid_property
    def days_left(self):
        if not self.deadline_at:
            return None
        delta = self.deadline_at.date() - datetime.utcnow().date()
        return delta.days

    @hybrid_property
    def is_overdue(self):
        if not self.deadline_at:
            return False
        return datetime.utcnow() > self.deadline_at

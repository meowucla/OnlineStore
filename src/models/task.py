# src/models/task.py
from dataclasses import dataclass
from typing import Optional
from .enums import TaskStatus

@dataclass
class Task:
    id: int
    source_id: int
    timestamp: float
    status: TaskStatus = TaskStatus.PENDING
    time_assigned_to_device: Optional[float] = None
    time_left_buffer: Optional[float] = None
    time_completed: Optional[float] = None

    def __hash__(self):
        return self.id

    def __lt__(self, other):
        # Для приоритетной очереди, сортировка по времени поступления (FIFO)
        return self.timestamp < other.timestamp
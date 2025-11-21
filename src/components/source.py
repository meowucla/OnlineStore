# src/components/source.py
from typing import Optional
from ..interfaces.i_source import ITaskSource
from ..models.task import Task

class Source(ITaskSource):
    def __init__(self, source_id: int, generation_interval: float = 1.0):
        self.id = source_id
        self.generation_interval = generation_interval
        self.last_generation_time = 0.0
        self.next_task_id = 1

    def get_next_generation_time(self) -> float:
        return self.last_generation_time + self.generation_interval

    def generate_task(self, current_time: float) -> Optional[Task]:
        if current_time >= self.get_next_generation_time():
            task = Task(
                id=self.next_task_id,
                source_id=self.id,
                timestamp=current_time
            )
            self.next_task_id += 1
            self.last_generation_time = current_time
            return task
        return None
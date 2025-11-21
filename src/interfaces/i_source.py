# src/interfaces/i_source.py
from abc import ABC, abstractmethod
from typing import Optional
from ..models.task import Task

class ITaskSource(ABC):
    @abstractmethod
    def generate_task(self, current_time: float) -> Optional[Task]:
        pass

    @abstractmethod
    def get_next_generation_time(self) -> float:
        pass
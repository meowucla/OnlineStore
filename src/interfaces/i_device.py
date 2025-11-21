# src/interfaces/i_device.py
from abc import ABC, abstractmethod
from typing import Optional
from ..models.task import Task

class IDevice(ABC):
    @abstractmethod
    def is_free(self) -> bool:
        pass

    @abstractmethod
    def assign_task(self, task: Task, current_time: float) -> float:
        pass

    @abstractmethod
    def complete_task(self) -> Task:
        pass

    @abstractmethod
    def get_id(self) -> int:
        pass
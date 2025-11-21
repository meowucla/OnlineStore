# src/interfaces/i_buffer.py
from abc import ABC, abstractmethod
from typing import Optional
from ..models.task import Task

class IBuffer(ABC):
    @abstractmethod
    def enqueue(self, task: Task, current_time: float) -> bool:
        """Возвращает True, если задача помещена успешно."""
        pass

    @abstractmethod
    def dequeue(self, current_time: float) -> Optional[Task]:
        """Возвращает задачу, выбранную из буфера."""
        pass

    @abstractmethod
    def is_full(self) -> bool:
        pass

    @abstractmethod
    def is_empty(self) -> bool:
        pass

    @abstractmethod
    def apply_replacement_policy(self, current_time: float) -> Optional[Task]:
        """Возвращает вытесненную задачу."""
        pass

    @abstractmethod
    def get_state(self) -> str:
        """Возвращает строковое описание текущего состояния буфера."""
        pass

    @abstractmethod
    def get_pointer_pos(self) -> int:
        """Возвращает текущую позицию указателя для дисциплин, использующих его."""
        pass
# src/components/buffer.py
from typing import List, Optional
from ..interfaces.i_buffer import IBuffer
from ..models.task import Task
from ..models.enums import TaskStatus


class Buffer(IBuffer):
    def __init__(self, max_size: int, buffer_type: str = "ring"):
        self.max_size = max_size
        self.buffer_type = buffer_type
        if self.buffer_type == "ring":
            self.ring_buffer: List[Optional[Task]] = [None] * max_size
            self.pointer = 0  # Указатель для заполнения (Д10З1)
        else:
            raise NotImplementedError(f"Buffer type {self.buffer_type} not implemented")

    def is_full(self) -> bool:
        if self.buffer_type == "ring":
            return all(t is not None for t in self.ring_buffer)
        return False

    def is_empty(self) -> bool:
        if self.buffer_type == "ring":
            return all(t is None for t in self.ring_buffer)
        return True

    def get_pointer_pos(self) -> int:
        return self.pointer

    def enqueue(self, task: Task, current_time: float) -> bool:
        if self.buffer_type == "ring":
            initial_ptr = self.pointer
            while self.ring_buffer[self.pointer] is not None:
                self.pointer = (self.pointer + 1) % self.max_size
                if self.pointer == initial_ptr:  # Кольцо пройдено, мест нет
                    return False  # Не удалось поставить в очередь

            self.ring_buffer[self.pointer] = task
            task.status = TaskStatus.BUFFERED
            self.pointer = (self.pointer + 1) % self.max_size  # Указатель указывает на следующее место
            return True
        return False

    def apply_replacement_policy(self, current_time: float) -> Optional[Task]:
        # Дисциплина отказа Д10О1: под указателем.
        # Указатель не сдвигается, если буфер полон.
        # Заявка под указателем вытесняется.
        if self.buffer_type == "ring":
            if self.ring_buffer[self.pointer] is not None:
                replaced_task = self.ring_buffer[self.pointer]
                self.ring_buffer[self.pointer] = None
                replaced_task.status = TaskStatus.ASSIGNED
                replaced_task.time_completed = current_time
                task_to_place = Task(
                    id=-1,
                    source_id=-1,
                    timestamp=current_time,
                    status=TaskStatus.BUFFERED
                )
                self.ring_buffer[self.pointer] = task_to_place
                self.pointer = (self.pointer + 1) % self.max_size  # Сдвигаем указатель
                return replaced_task
        return None

    def dequeue(self, current_time: float) -> Optional[Task]:
        # Дисциплина выбора заявок Д2Б1: FIFO.
        # В кольцевом буфере FIFO означает, что нужно искать самую старую задачу.
        # Это делается за O(n), где n - размер буфера.
        if self.buffer_type == "ring":
            oldest_task: Optional[Task] = None
            oldest_idx = -1
            for i, task in enumerate(self.ring_buffer):
                if task is not None:
                    if oldest_task is None or task.timestamp < oldest_task.timestamp:
                        oldest_task = task
                        oldest_idx = i

            if oldest_task:
                self.ring_buffer[oldest_idx] = None
                oldest_task.time_left_buffer = current_time
                return oldest_task
        return None

    def get_state(self) -> str:
        if self.buffer_type == "ring":
            # Показываем содержимое буфера и позицию указателя
            buffer_str = []
            for i, task in enumerate(self.ring_buffer):
                if task is None:
                    buffer_str.append("Empty")
                else:
                    buffer_str.append(f"({task.source_id},{task.id})")
            pointer_str = f"Pointer: {self.pointer}"
            return f"{buffer_str} | {pointer_str}"
        return ""
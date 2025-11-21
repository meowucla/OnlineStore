# src/components/device.py
import random
from typing import Optional
from ..interfaces.i_device import IDevice
from ..models.task import Task
from ..models.enums import TaskStatus


class Device(IDevice):
    def __init__(self, device_id: int, service_time_min: float = 1.0, service_time_max: float = 2.0):
        self.id = device_id
        self.device_id = device_id
        self.current_task: Optional[Task] = None
        self.service_time_min = service_time_min
        self.service_time_max = service_time_max
        self.busy_until_time: float = 0.0

    def get_id(self) -> int:
        return self.id

    def is_free(self) -> bool:
        return self.current_task is None

    def assign_task(self, task: Task, current_time: float) -> float:
        if not self.is_free():
            raise RuntimeError(f"Device {self.id} is not free!")

        self.current_task = task
        task.status = TaskStatus.ASSIGNED
        task.time_assigned_to_device = current_time

        # Время обслуживания равномерно (П32)
        service_duration = random.uniform(self.service_time_min, self.service_time_max)
        self.busy_until_time = current_time + service_duration
        return self.busy_until_time

    def complete_task(self) -> Task:
        if self.is_free():
            raise RuntimeError(f"Device {self.id} is free, no task to complete!")
        completed_task = self.current_task
        completed_task.status = TaskStatus.COMPLETED
        completed_task.time_completed = self.busy_until_time
        self.current_task = None
        self.busy_until_time = 0.0
        return completed_task
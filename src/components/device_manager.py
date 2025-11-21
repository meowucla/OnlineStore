# src/components/device_manager.py
from typing import List, Optional
from ..interfaces.i_device import IDevice

class DeviceManager:
    def __init__(self):
        self.devices: List[IDevice] = []

    def add_device(self, d: IDevice):
        self.devices.append(d)
        # Сортируем приборы по ID для Д2П1 (приоритет по номеру прибора)
        self.devices.sort(key=lambda dev: dev.get_id())

    def find_free_device(self) -> Optional[IDevice]:
        # Дисциплина выбора прибора Д2П1: приоритет по номеру прибора.
        # Перебор начинается с самого приоритетного (с наименьшим ID).
        for device in self.devices:
            if device.is_free():
                return device
        return None
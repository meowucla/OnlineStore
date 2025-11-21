# src/components/dispatcher.py
import heapq
from typing import List, Optional, Dict, Tuple
from collections import defaultdict
from ..models.task import Task
from ..models.enums import EventType, TaskStatus
from ..interfaces.i_buffer import IBuffer
from ..interfaces.i_device import IDevice
from .device_manager import DeviceManager


class Dispatcher:
    def __init__(self, buffer: IBuffer, device_manager: DeviceManager):
        # self.warehouse = warehouse # Убрано
        self.buffer = buffer
        self.device_manager = device_manager
        self.current_time = 0.0
        self.event_calendar: List[Tuple[float, int, EventType, Optional[object]]] = []  # Добавлен уникальный ID события
        self.event_counter = 0  # Счетчик для уникального ID
        # Статистика
        self.stats = {
            "generated_by_source": defaultdict(int),
            "rejected_by_source": defaultdict(int),
            "total_time_in_system_by_source": defaultdict(float),
            "total_time_in_buffer_by_source": defaultdict(float),
            "total_service_time_by_source": defaultdict(float),
            "service_times": defaultdict(list),
            "wait_times": defaultdict(list),
        }
        # Словарь для отслеживания задач, находящихся в системе
        self.active_tasks: Dict[int, Task] = {}
        # Для отслеживания оставшегося количества генераций
        self.sources_to_generate = {}

    def schedule_event(self, time: float, event_type: EventType, data: Optional[object] = None):
        # Используем event_counter как уникальный идентификатор, чтобы избежать сравнения EventType
        heapq.heappush(self.event_calendar, (time, self.event_counter, event_type, data))
        self.event_counter += 1

    def initialize_sources(self, sources, num_tasks_to_generate_per_source: int):
        # Инициализируем ТОЛЬКО первое событие генерации для каждого источника
        # и отслеживаем, сколько задач уже сгенерировано
        self.sources_to_generate = {source.id: num_tasks_to_generate_per_source for source in sources}
        for source in sources:
            next_gen_time = source.get_next_generation_time()
            # Передаем сам источник и его оставшееся количество генераций
            self.schedule_event(next_gen_time, EventType.GENERATE_TASK, (source, self.sources_to_generate[source.id]))

    def run_step(self) -> bool:
        """
        Выполняет один шаг моделирования (обрабатывает одно ближайшее событие).
        Возвращает False, если календарь событий пуст.
        """
        if not self.event_calendar:
            return False

        event_time, _, event_type, event_data = heapq.heappop(
            self.event_calendar)  # Извлекаем уникальный ID, но не используем
        self.current_time = event_time
        print(f"\n--- Шаг моделирования ---")
        print(f"Текущее модельное время: {self.current_time:.2f}")
        print(f"Событие: {event_type.value}")
        print(f"Данные события: {event_data}")

        if event_type == EventType.GENERATE_TASK:
            source_data = event_data
            if isinstance(source_data, tuple) and len(source_data) == 2:
                source = source_data[0]
                remaining_count = source_data[1]
                if remaining_count > 0:
                    task = source.generate_task(self.current_time)
                    if task:
                        self.active_tasks[task.id] = task
                        self.stats["generated_by_source"][task.source_id] += 1
                        print(f"  Сгенерирована заявка: ID {task.id}, Источник {task.source_id}")
                        # Планируем событие поступления задачи к диспетчеру
                        self.schedule_event(self.current_time, EventType.TASK_ARRIVES_AT_DISPATCHER, task)

                        # Обновляем оставшееся количество и планируем следующую генерацию
                        self.sources_to_generate[source.id] -= 1
                        if self.sources_to_generate[source.id] > 0:
                            next_gen_time = source.get_next_generation_time()
                            if next_gen_time > self.current_time:  # Проверяем, чтобы не было дубликатов
                                self.schedule_event(next_gen_time, EventType.GENERATE_TASK,
                                                    (source, self.sources_to_generate[source.id]))
                        else:
                            print(f"  Источник {source.id} завершил генерацию заявок.")
                else:
                    print(f"  Попытка генерации от источника {source_data[0].id}, но лимит исчерпан.")

        elif event_type == EventType.TASK_ARRIVES_AT_DISPATCHER:
            task: Task = event_data
            print(f"  Заявка {task.id} от источника {task.source_id} поступила к диспетчеру.")
            # Сразу направляем в буфер
            print(f"  Направляем заявку {task.id} в буфер.")
            # Попытка поместить в буфер
            if self.buffer.is_full():
                print(f"  Буфер полон! Применяем дисциплину вытеснения.")
                replaced_task = self.buffer.apply_replacement_policy(self.current_time)
                if replaced_task:
                    print(f"  Заявка {replaced_task.id} (источник {replaced_task.source_id}) вытеснена из буфера.")
                    self.stats["rejected_by_source"][replaced_task.source_id] += 1
                    self.active_tasks.pop(replaced_task.id, None)  # Убираем из активных
                    self.schedule_event(self.current_time, EventType.TASK_REPLACED_IN_BUFFER, replaced_task)
                else:
                    print(f"  Ошибка: буфер полон, но не удалось вытеснить задачу.")
            else:
                success = self.buffer.enqueue(task, self.current_time)
                if success:
                    print(f"  Заявка {task.id} помещена в буфер.")
                    self.schedule_event(self.current_time, EventType.TASK_ENTERED_BUFFER, task)
                else:
                    print(f"  Ошибка: не удалось поместить задачу {task.id} в буфер, несмотря на проверку.")

        elif event_type == EventType.TASK_ENTERED_BUFFER:
            task: Task = event_data
            print(f"  Заявка {task.id} официально в буфере.")
            free_device = self.device_manager.find_free_device()
            if free_device and not self.buffer.is_empty():
                task_to_assign = self.buffer.dequeue(self.current_time)
                if task_to_assign:
                    print(f"  Выбрана заявка {task_to_assign.id} из буфера для обслуживания (FIFO).")
                    completion_time = free_device.assign_task(task_to_assign, self.current_time)
                    print(f"  Заявка {task_to_assign.id} назначена на прибор {free_device.get_id()}.")
                    self.schedule_event(completion_time, EventType.TASK_COMPLETED_BY_DEVICE,
                                        (task_to_assign, free_device))
                    self.schedule_event(self.current_time, EventType.TASK_ASSIGNED_TO_DEVICE,
                                        (task_to_assign, free_device))
                else:
                    print(f"  Ошибка: буфер пуст при попытке выбора задачи, хотя только что была задача.")


        elif event_type == EventType.TASK_REPLACED_IN_BUFFER:
            replaced_task: Task = event_data
            # Обновляем статистику для вытесненной задачи
            time_in_system = replaced_task.time_completed - replaced_task.timestamp
            self.stats["total_time_in_system_by_source"][replaced_task.source_id] += time_in_system
            # Время в буфере для вытесненной не считаем, так как она не была обслужена
            self.active_tasks.pop(replaced_task.id, None)  # Убираем из активных

        elif event_type == EventType.DEVICE_BECAME_FREE:
            device: IDevice = event_data
            print(f"  Прибор {device.get_id()} освободился.")
            # Попытка выбрать задачу из буфера и назначить на прибор
            task_to_assign = self.buffer.dequeue(self.current_time)
            if task_to_assign:
                print(f"  Выбрана заявка {task_to_assign.id} из буфера для обслуживания (FIFO).")
                completion_time = device.assign_task(task_to_assign, self.current_time)
                print(f"  Заявка {task_to_assign.id} назначена на прибор {device.get_id()}.")
                self.schedule_event(completion_time, EventType.TASK_COMPLETED_BY_DEVICE, (task_to_assign, device))
                self.schedule_event(self.current_time, EventType.TASK_ASSIGNED_TO_DEVICE, (task_to_assign, device))
            else:
                print(f"  Буфер пуст, прибор {device.get_id()} ожидает.")

        elif event_type == EventType.TASK_ASSIGNED_TO_DEVICE:
            task_data: Tuple[Task, IDevice] = event_data
            task, device = task_data
            print(f"  Подтверждение назначения задачи {task.id} на прибор {device.get_id()}.")

        elif event_type == EventType.TASK_COMPLETED_BY_DEVICE:
            task_data: Tuple[Task, IDevice] = event_data
            task, device = task_data
            completed_task = device.complete_task()
            print(f"  Заявка {completed_task.id} обслужена прибором {device.get_id()}.")

            # Обновляем статистику для завершенной задачи
            time_in_system = completed_task.time_completed - completed_task.timestamp
            time_in_buffer = (
                        completed_task.time_left_buffer - completed_task.timestamp) if completed_task.time_left_buffer else 0
            time_in_service = completed_task.time_completed - completed_task.time_assigned_to_device

            self.stats["total_time_in_system_by_source"][completed_task.source_id] += time_in_system
            self.stats["total_time_in_buffer_by_source"][completed_task.source_id] += time_in_buffer
            self.stats["total_service_time_by_source"][completed_task.source_id] += time_in_service

            self.stats["service_times"][completed_task.source_id].append(time_in_service)
            self.stats["wait_times"][completed_task.source_id].append(time_in_buffer)

            # Убираем задачу из активных
            self.active_tasks.pop(completed_task.id, None)

            # Планируем событие освобождения прибора, чтобы он мог принять следующую задачу
            self.schedule_event(self.current_time, EventType.DEVICE_BECAME_FREE, device)

        self.print_current_state()
        return True

    def print_current_state(self):
        print("\n--- Текущее состояние системы ---")
        print(f"Модельное время: {self.current_time:.2f}")
        # Печатаем ближайшие 5 событий, исключая уникальный ID из вывода
        upcoming_events = [(time, et.value, data) for time, _, et, data in self.event_calendar[:5]]
        print(f"Календарь событий (ближайшие 5): {upcoming_events}")
        print(f"Состояние буфера: {self.buffer.get_state()}")
        print(f"Позиция указателя буфера: {self.buffer.get_pointer_pos()}")
        print("Состояние приборов:")
        for dev in self.device_manager.devices:
            if dev.is_free():
                print(f"  Прибор {dev.get_id()}: Свободен")
            else:
                print(
                    f"  Прибор {dev.get_id()}: Занят задачей {dev.current_task.id if dev.current_task else 'None'} до времени {dev.busy_until_time:.2f}")
        print("Активные задачи (в системе):")
        for tid, t in self.active_tasks.items():
            print(f"  ID {t.id}, Источник {t.source_id}, Статус {t.status.value}, Время поступления {t.timestamp:.2f}")
        print("Частичная статистика (сгенерировано/отказано):")
        for src_id in self.stats["generated_by_source"]:
            gen = self.stats["generated_by_source"][src_id]
            rej = self.stats["rejected_by_source"][src_id]
            print(f"  Источник {src_id}: {gen} / {rej}")
        print("--- Конец состояния ---\n")
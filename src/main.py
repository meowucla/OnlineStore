# src/main.py
from .components import Source, Buffer, Device, DeviceManager, Dispatcher
from .models import TaskStatus


def main():
    print("=== Запуск пошаговой модели СМО ===")

    # Настройка параметров модели
    NUM_SOURCES = 1
    NUM_DEVICES = 1
    BUFFER_SIZE = 3
    GENERATION_INTERVAL = 2.0
    SERVICE_TIME_MIN = 1.0
    SERVICE_TIME_MAX = 3.0
    NUM_TASKS_TO_GENERATE_PER_SOURCE = 5

    # Создание компонентов
    sources = [Source(i + 1, generation_interval=GENERATION_INTERVAL) for i in range(NUM_SOURCES)]
    buffer = Buffer(max_size=BUFFER_SIZE, buffer_type="ring")
    device_manager = DeviceManager()

    for i in range(NUM_DEVICES):
        device = Device(device_id=i + 1, service_time_min=SERVICE_TIME_MIN, service_time_max=SERVICE_TIME_MAX)
        device_manager.add_device(device)

    dispatcher = Dispatcher(buffer, device_manager)

    # Инициализация событий
    dispatcher.initialize_sources(sources, NUM_TASKS_TO_GENERATE_PER_SOURCE)

    # Запуск пошагового моделирования
    step_count = 0
    max_steps = 50  # Ограничение на количество шагов для отладки
    while dispatcher.run_step() and step_count < max_steps:
        step_count += 1
        input("Нажмите Enter для следующего шага...")

    print("\n=== Моделирование завершено ===")
    print(f"Всего выполнено шагов: {step_count}")
    print("\nФинальная статистика (частичная):")
    print(f"Сгенерировано заявок: {dict(dispatcher.stats['generated_by_source'])}")
    print(f"Отказано заявок: {dict(dispatcher.stats['rejected_by_source'])}")
    print(f"Среднее время в системе: ", end="")
    for src_id in dispatcher.stats["total_time_in_system_by_source"]:
        total_time = dispatcher.stats["total_time_in_system_by_source"][src_id]
        count = dispatcher.stats["generated_by_source"][src_id]
        avg_time = total_time / count if count > 0 else 0
        print(f"И{src_id}: {avg_time:.2f} ", end="")
    print("\nСреднее время в буфере: ", end="")
    for src_id in dispatcher.stats["total_time_in_buffer_by_source"]:
        total_time = dispatcher.stats["total_time_in_buffer_by_source"][src_id]
        count = dispatcher.stats["generated_by_source"][src_id]
        avg_time = total_time / count if count > 0 else 0
        print(f"И{src_id}: {avg_time:.2f} ", end="")
    print("\nСреднее время обслуживания: ", end="")
    for src_id in dispatcher.stats["total_service_time_by_source"]:
        total_time = dispatcher.stats["total_service_time_by_source"][src_id]
        count = dispatcher.stats["generated_by_source"][src_id]
        avg_time = total_time / count if count > 0 else 0
        print(f"И{src_id}: {avg_time:.2f} ", end="")
    print("\n---")


if __name__ == "__main__":
    main()
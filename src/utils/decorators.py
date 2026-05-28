import time
import logging
import asyncio
import functools

logger = logging.getLogger("app_logger")


def log_async_time(func):
    """
    Декоратор, который замеряет время выполнения Async функции.
    """

    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        result = await func(*args, **kwargs)
        execution_time = time.perf_counter() - start_time
        logger.info(f"Async функция [{func.__name__}] выполнена за {execution_time:.4f} сек.")
        return result

    return wrapper


# До лучших времён
# def log_sync_time(func):
#     """
#     Декораторый, который замеряет время выполнения Sync функции.
#     """
#     @functools.wraps(func)
#     def wrapper(*args, **kwargs):
#         start_time = time.perf_counter()
#         result = func(*args, **kwargs)
#         execution_time = time.perf_counter() - start_time
#         logger.info(f"Sync функция [{func.__name__}] выполнена за {execution_time:.4f} сек.")

def retry(retries: int = 3, delay: float = 1.0):
    """
    Декоратор с параметрами.
    Повторяет выполнение async функции при падении.
    """

    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            if retries <= 0:
                raise ValueError("Количество попыток должно быть больше 0")

            for attempt in range(1, retries + 1):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    logger.warning(f"Ошибка в {func.__name__} (Попытка {attempt}/{retries}): {e}")

                    if attempt >= retries:
                        raise e

                    await asyncio.sleep(delay)

            raise RuntimeError("Непредвиденное завершение цикла повторных попыток")

        return wrapper

    return decorator

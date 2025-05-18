import os
import requests
from flask import current_app
from app import cache # Используем существующий экземпляр cache из __init__.py

# Базовый URL для API exchangerate-api.com
API_BASE_URL = "https://v6.exchangerate-api.com/v6"

class ExchangeRateService:
    @staticmethod
    @cache.memoize(timeout=3600) # Кэшировать результат на 1 час (3600 секунд)
    def get_exchange_rate(base_currency: str, target_currency: str) -> float:
        """
        Получает обменный курс между двумя валютами.

        :param base_currency: Базовая валюта (например, 'USD')
        :param target_currency: Целевая валюта (например, 'RUB')
        :return: Обменный курс (float). Например, если курс USD/RUB = 75.0, вернет 75.0.
                 Возвращает 1.0, если базовая и целевая валюты совпадают.
                 Вызывает исключение ValueError при ошибке API или если валюты не найдены.
        """
        if base_currency.upper() == target_currency.upper():
            return 1.0

        api_key = os.getenv('EXCHANGE_RATE_API_KEY')
        if not api_key:
            current_app.logger.error("EXCHANGE_RATE_API_KEY не найден в переменных окружения.")
            raise ValueError("API ключ для обменных курсов не настроен.")

        url = f"{API_BASE_URL}/{api_key}/pair/{base_currency.upper()}/{target_currency.upper()}"
        
        try:
            response = requests.get(url, timeout=10) # Таймаут 10 секунд
            response.raise_for_status()  # Вызовет исключение для HTTP ошибок 4xx/5xx
            data = response.json()

            if data.get('result') == 'success':
                rate = data.get('conversion_rate')
                if rate is not None:
                    current_app.logger.info(f"Получен курс: 1 {base_currency} = {rate} {target_currency}")
                    return float(rate)
                else:
                    current_app.logger.error(f"Ключ 'conversion_rate' отсутствует в ответе API для {base_currency}/{target_currency}. Ответ: {data}")
                    raise ValueError(f"Не удалось получить курс для {base_currency}/{target_currency}: ключ 'conversion_rate' отсутствует.")
            else:
                error_type = data.get('error-type', 'unknown_error')
                current_app.logger.error(f"Ошибка API exchangerate: {error_type} для {base_currency}/{target_currency}. Ответ: {data}")
                # Предоставляем более информативное сообщение пользователю/разработчику
                if error_type == "invalid-key":
                    raise ValueError("Недействительный API ключ для exchangerate-api.com.")
                elif error_type == "inactive-account":
                    raise ValueError("Аккаунт exchangerate-api.com неактивен.")
                elif error_type == "unsupported-code":
                     raise ValueError(f"Одна из валют ({base_currency} или {target_currency}) не поддерживается API.")
                else:
                    raise ValueError(f"Ошибка API при получении курса для {base_currency}/{target_currency}: {error_type}")

        except requests.exceptions.RequestException as e:
            current_app.logger.error(f"Ошибка запроса к API обменных курсов для {base_currency}/{target_currency}: {e}")
            raise ValueError(f"Сетевая ошибка при получении курса для {base_currency}/{target_currency}.")
        except ValueError as e: # Перехватываем ValueError, которые мы сами генерируем выше
            # Логгируем и снова выбрасываем, чтобы не попасть в общий Exception ниже с менее специфичным сообщением
            current_app.logger.error(f"Ошибка значения при обработке ответа API для {base_currency}/{target_currency}: {e}")
            raise
        except Exception as e: # Общий обработчик для других неожиданных ошибок (например, json.JSONDecodeError)
            current_app.logger.error(f"Неожиданная ошибка при получении курса для {base_currency}/{target_currency}: {e}")
            raise ValueError(f"Неожиданная ошибка при получении курса для {base_currency}/{target_currency}.")

# Пример использования (можно раскомментировать для тестирования)
# if __name__ == '__main__':
#     # Для прямого запуска этого файла нужно мокнуть os.getenv и current_app.logger, 
#     # или настроить окружение для Flask приложения.
#     # Этот пример не будет работать без контекста приложения Flask для cache и logger.
#     class MockApp:
#         def __init__(self):
#             self.logger = MockLogger()
#     class MockLogger:
#         def error(self, msg): print(f"ERROR: {msg}")
#         def info(self, msg): print(f"INFO: {msg}")
#     
#     # Загружаем .env файл, если он есть в текущей или родительской директории
#     from dotenv import load_dotenv
#     # Предполагаем, что .env находится в корне проекта, а этот скрипт в backend/app/services
#     dotenv_path = os.path.join(os.path.dirname(__file__), '..', '..', '.env')
#     print(f"Пытаюсь загрузить .env из: {dotenv_path}")
#     load_dotenv(dotenv_path=dotenv_path)
# 
#     # Простая имитация Flask cache для теста
#     class MockCache:
#         def memoize(self, timeout):
#             def decorator(f):
#                 return f
#             return decorator
#     cache = MockCache()
# 
#     # Мок current_app для логгера
#     current_app = MockApp()
# 
#     print(f"API Key from env: {os.getenv('EXCHANGE_RATE_API_KEY')}") # Проверка загрузки ключа
# 
#     try:
#         usd_to_rub = ExchangeRateService.get_exchange_rate('USD', 'RUB')
#         print(f"1 USD = {usd_to_rub} RUB")
# 
#         eur_to_usd = ExchangeRateService.get_exchange_rate('EUR', 'USD')
#         print(f"1 EUR = {eur_to_usd} USD")
# 
#         # Тест одинаковых валют
#         usd_to_usd = ExchangeRateService.get_exchange_rate('USD', 'USD')
#         print(f"1 USD = {usd_to_usd} USD")
# 
#         # Тест с ошибкой (несуществующая валюта)
#         # usd_to_xyz = ExchangeRateService.get_exchange_rate('USD', 'XYZ') 
#         # print(f"1 USD = {usd_to_xyz} XYZ")
# 
#     except ValueError as e:
#         print(f"Ошибка получения курса: {e}")
#     except Exception as e:
#         print(f"Неожиданная общая ошибка: {e}") 
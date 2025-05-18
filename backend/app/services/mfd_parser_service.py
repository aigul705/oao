import requests
from bs4 import BeautifulSoup
from datetime import datetime
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MfdParserService:
    BASE_URL = "https://mfd.ru/centrobank/preciousmetals/"

    # Используем фиксированный порядок и имена металлов, как они обычно идут на сайте ЦБ
    # Первый столбец (индекс 0) - Дата
    # Далее металлы по порядку:
    METAL_ORDER = ["Gold", "Silver", "Platinum", "Palladium"]
    # Соответствующие ключи из METAL_NAME_MAP, которые мы использовали ранее, для удобства
    # можно было бы просто использовать METAL_ORDER напрямую, если он совпадает с ожидаемыми именами в init_db
    # "Золото": "Gold", "Серебро": "Silver", "Платина": "Platinum", "Палладий": "Palladium"

    def fetch_historical_data(self):
        """
        Получает исторические данные о ценах на драгоценные металлы с mfd.ru.
        Использует фиксированный порядок столбцов для металлов.
        Возвращает список словарей, где каждый словарь содержит:
        {
            "date": datetime.date,
            "metal_name": str, (English name from METAL_ORDER)
            "price": float (RUB per gram)
        }
        """
        try:
            response = requests.get(self.BASE_URL, timeout=10)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка при запросе к mfd.ru: {e}")
            return []

        soup = BeautifulSoup(response.content, 'html.parser')
        
        data_table = None
        all_tables = soup.find_all('table')
        
        if not all_tables:
            logger.warning("На странице mfd.ru не найдено таблиц.")
            return []

        # Предполагаем, что нужная таблица - вторая на странице
        if len(all_tables) > 1:
            data_table = all_tables[1] 
        else:
            logger.warning("На странице mfd.ru найдено менее двух таблиц, не могу определить таблицу с данными.")
            return []

        if not data_table:
            logger.warning("Не удалось найти таблицу с данными на mfd.ru (после выбора all_tables[1]).")
            return []

        rows = data_table.find_all('tr')
        # Ожидаем как минимум строку заголовков (которую мы пропустим) и одну строку данных
        if not rows or len(rows) < 2: 
            logger.warning("Таблица с данными на mfd.ru пуста или не содержит строк данных (rows < 2).")
            return []

        historical_prices = []
        
        # Пропускаем первую строку (rows[0]), предполагая, что это заголовки.
        # Начинаем обработку со второй строки (rows[1]).
        for row_idx, row in enumerate(rows[1:]):
            cols = row.find_all('td')
            
            # Ожидаем как минимум 5 столбцов: Дата + 4 металла
            if len(cols) < 5:
                logger.warning(f"В строке {row_idx + 1} недостаточно столбцов ({len(cols)}), пропускаем.")
                continue

            try:
                date_str = cols[0].get_text(strip=True)
                date_obj = datetime.strptime(date_str, '%d.%m.%Y').date()
            except ValueError:
                logger.warning(f"Не удалось распознать дату: '{date_str}' в строке {row_idx + 1}. Содержимое: {[c.get_text(strip=True) for c in cols]}")
                continue

            # Обрабатываем столбцы металлов по фиксированному порядку
            for metal_idx, metal_name_en in enumerate(self.METAL_ORDER):
                # Индекс столбца для текущего металла: metal_idx + 1 (т.к. столбец 0 - дата)
                col_index_for_metal = metal_idx + 1
                if col_index_for_metal < len(cols):
                    try:
                        price_str = cols[col_index_for_metal].get_text(strip=True)
                        price_str_cleaned = price_str.replace('\xa0', '').replace(' ', '')
                        if not price_str_cleaned: # Проверка на пустую строку после очистки
                             logger.warning(f"Пустая цена для {metal_name_en} на дату {date_str} в строке {row_idx + 1}, столбец {col_index_for_metal + 1}.")
                             continue
                        price = float(price_str_cleaned)
                        
                        historical_prices.append({
                            "date": date_obj,
                            "metal_name": metal_name_en, # "Gold", "Silver", etc.
                            "price": price
                        })
                    except ValueError:
                        logger.warning(f"Не удалось преобразовать цену '{price_str}' для {metal_name_en} на дату {date_str} в число. Строка {row_idx + 1}.")
                        continue
                    except IndexError:
                        # Это не должно произойти из-за проверки `col_index_for_metal < len(cols)`
                        logger.error(f"Ошибка индекса при попытке получить цену для {metal_name_en} на дату {date_str}. Это неожиданно.")
                        continue
                else:
                    logger.warning(f"Недостаточно столбцов для металла {metal_name_en} (ожидался индекс {col_index_for_metal}) в строке {row_idx + 1} (всего столбцов: {len(cols)}).")

        if historical_prices:
            logger.info(f"Успешно загружено {len(historical_prices)} записей с mfd.ru (используя фиксированный порядок столбцов).")
        else:
            logger.warning("Не удалось загрузить ни одной записи с mfd.ru (используя фиксированный порядок столбцов). Проверьте логи выше.")
            
        return historical_prices

if __name__ == '__main__':
    # Пример использования
    parser = MfdParserService()
    data = parser.fetch_historical_data()
    if data:
        # Вывести первые 5 и последние 5 записей для проверки
        print("Первые 5 записей:")
        for item in data[:5]: 
            print(item)
        if len(data) > 5:
            print("\nПоследние 5 записей:")
            for item in data[-5:]:
                print(item)
        print(f"\nВсего записей: {len(data)}")
    else:
        print("Не удалось получить данные.") 
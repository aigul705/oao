from datetime import datetime, timedelta
from typing import List, Dict, Optional
import statistics
import json
import os
from flask import current_app
from app import db
from app.models.metal import Metal, MetalPrice, MetalAnalysis
from app.services.alpha_vantage_service import MetalParserService
from app.services.exchange_rate_service import ExchangeRateService

# Определяем путь к директории Data Lake и файлу лога
DATA_LAKE_DIR = os.path.join(os.path.dirname(__file__), '..', 'data_lake') # Папка data_lake будет в backend/data_lake
PRICE_LOG_FILE = os.path.join(DATA_LAKE_DIR, 'price_log.json')

# Базовая валюта, в которой хранятся цены в БД (по умолчанию)
DEFAULT_BASE_CURRENCY = "USD"

class MetalService:
    @staticmethod
    def get_current_prices(target_currency: Optional[str] = None) -> List[Dict]:
        """Get current prices for all metals, optionally converting to a target currency."""
        metals = Metal.query.all()
        current_prices_output = []
        
        # Определяем целевую валюту. Если не указана, используем базовую (USD).
        final_target_currency = target_currency.upper() if target_currency else DEFAULT_BASE_CURRENCY

        for metal in metals:
            latest_price_record = MetalPrice.query.filter_by(metal_id=metal.id)\
                .order_by(MetalPrice.timestamp.desc())\
                .first()
            
            if latest_price_record:
                price_value = latest_price_record.price
                price_unit = metal.unit # Изначально, например, "USD/oz"
                # Предполагаем, что metal.unit всегда содержит базовую валюту в начале, например, "USD/oz"
                # Это нужно для корректной конвертации.
                # Если metal.unit может быть другим, логику извлечения базовой валюты нужно будет усложнить.
                original_price_currency = metal.unit.split('/')[0] if '/' in metal.unit else DEFAULT_BASE_CURRENCY

                if final_target_currency != original_price_currency:
                    try:
                        # Получаем курс для конвертации из исходной валюты цены в целевую
                        rate = ExchangeRateService.get_exchange_rate(original_price_currency, final_target_currency)
                        price_value = round(price_value * rate, 2) # Округляем до 2 знаков после запятой
                        # Обновляем единицу измерения
                        if '/' in price_unit:
                            price_suffix = price_unit.split('/', 1)[1]
                            price_unit = f"{final_target_currency}/{price_suffix}"
                        else:
                            price_unit = final_target_currency # Если не было суффикса, просто ставим валюту
                        current_app.logger.info(f"Конвертирована цена для {metal.symbol}: {latest_price_record.price} {original_price_currency} -> {price_value} {final_target_currency} (курс: {rate})")
                    except ValueError as e:
                        # Если не удалось получить курс, логгируем ошибку и возвращаем цену в исходной валюте
                        current_app.logger.error(f"Не удалось конвертировать цену для {metal.symbol} в {final_target_currency}: {e}. Возвращаем исходную цену.")
                        # price_value и price_unit остаются без изменений
                current_prices_output.append({
                    'symbol': metal.symbol,
                    'name': metal.name,
                    'price': price_value,
                    'unit': price_unit,
                    'timestamp': latest_price_record.timestamp.isoformat()
                })
            else:
                # Если для металла нет цен, можно добавить запись с None или пропустить
                current_app.logger.warn(f"Нет данных о ценах для металла: {metal.symbol}")
                current_prices_output.append({
                    'symbol': metal.symbol,
                    'name': metal.name,
                    'price': None,
                    'unit': f"{final_target_currency}/oz" if '/' in metal.unit else final_target_currency, # Попытка указать целевую валюту
                    'timestamp': None
                })
        
        return current_prices_output

    @staticmethod
    def get_historical_prices(metal_symbol: str, date_from: datetime, date_to: datetime) -> List[Dict]:
        """Get historical prices for a specific metal within a date range."""
        metal = Metal.query.filter_by(symbol=metal_symbol.upper()).first()
        if not metal:
            return []

        prices = MetalPrice.query.filter(
            MetalPrice.metal_id == metal.id,
            MetalPrice.timestamp >= date_from,
            MetalPrice.timestamp <= date_to
        ).order_by(MetalPrice.timestamp.asc()).all()

        return [{
            'price': price.price,
            'timestamp': price.timestamp.isoformat()
        } for price in prices]

    @staticmethod
    def analyze_metal(metal_symbol: str) -> Dict:
        """Analyze metal price trends, volatility, and sentiment."""
        metal = Metal.query.filter_by(symbol=metal_symbol.upper()).first()
        if not metal:
            return {}

        # Get prices for the last 30 days
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=30)
        
        prices = MetalPrice.query.filter(
            MetalPrice.metal_id == metal.id,
            MetalPrice.timestamp >= start_date,
            MetalPrice.timestamp <= end_date
        ).order_by(MetalPrice.timestamp.asc()).all()

        if not prices:
            return {}

        # Calculate trend
        price_values = [p.price for p in prices]
        first_price = price_values[0]
        last_price = price_values[-1]
        price_change = ((last_price - first_price) / first_price) * 100

        if price_change > 1:
            trend = 'up'
        elif price_change < -1:
            trend = 'down'
        else:
            trend = 'unchanged'

        # Calculate volatility
        returns = [(price_values[i] - price_values[i-1])/price_values[i-1] 
                  for i in range(1, len(price_values))]
        volatility_value = statistics.stdev(returns) if len(returns) > 1 else 0

        if volatility_value > 0.02:  # 2% daily volatility threshold
            volatility = 'high'
        elif volatility_value > 0.01:  # 1% daily volatility threshold
            volatility = 'medium'
        else:
            volatility = 'low'

        # Determine sentiment based on trend and volatility
        if trend == 'up' and volatility != 'high':
            sentiment = 'positive'
        elif trend == 'down' and volatility != 'high':
            sentiment = 'negative'
        else:
            sentiment = 'neutral'

        # Store analysis in database
        analysis = MetalAnalysis(
            metal_id=metal.id,
            trend=trend,
            volatility=volatility,
            sentiment=sentiment,
            period_start=start_date,
            period_end=end_date
        )
        db.session.add(analysis)
        db.session.commit()

        return {
            'metal': metal_symbol,
            'trend': trend,
            'volatility': volatility,
            'sentiment': sentiment,
            'period_start': start_date.isoformat(),
            'period_end': end_date.isoformat()
        }

    @staticmethod
    def _log_prices_to_data_lake(prices_data: List[Dict]):
        """Вспомогательный метод для логирования цен в JSON файл."""
        try:
            # Создаем директорию data_lake, если она не существует
            if not os.path.exists(DATA_LAKE_DIR):
                os.makedirs(DATA_LAKE_DIR)
                print(f"Создана директория Data Lake: {DATA_LAKE_DIR}")
            
            # Записываем данные в файл. Каждая новая порция данных добавляется в виде нового объекта JSON.
            # Для простоты, будем дописывать в файл как последовательность JSON объектов (или список JSON объектов)
            # Более сложная реализация могла бы использовать JSON Lines или управлять большим JSON массивом.
            # Сейчас будем просто дописывать в файл, оборачивая каждую запись в список для простоты чтения как JSON.
            log_entry = {
                "log_timestamp": datetime.utcnow().isoformat(),
                "prices": prices_data
            }
            
            # Читаем существующие данные, если файл есть, или создаем новый список
            if os.path.exists(PRICE_LOG_FILE):
                with open(PRICE_LOG_FILE, 'r', encoding='utf-8') as f:
                    try:
                        current_log = json.load(f)
                        if not isinstance(current_log, list):
                            current_log = [current_log] # Если там был один объект, делаем список
                    except json.JSONDecodeError:
                        current_log = [] # Если файл пуст или поврежден
            else:
                current_log = []
            
            current_log.append(log_entry)
            
            with open(PRICE_LOG_FILE, 'w', encoding='utf-8') as f:
                json.dump(current_log, f, ensure_ascii=False, indent=4)
            print(f"Данные о ценах залогированы в {PRICE_LOG_FILE}")

        except Exception as e:
            print(f"Ошибка при логировании цен в Data Lake: {e}")

    @staticmethod
    def update_prices(prices_data: List[Dict]) -> None:
        """Update metal prices in the database."""
        saved_prices_info = []
        for price_data in prices_data:
            metal = Metal.query.filter_by(symbol=price_data['symbol'].upper()).first()
            if not metal:
                print(f"Металл с символом {price_data['symbol']} не найден в БД. Пропускаем обновление цены.")
                continue

            # Проверяем, есть ли уже цена для этого металла с такой же временной меткой
            existing_price = MetalPrice.query.filter_by(
                metal_id=metal.id,
                timestamp=datetime.fromisoformat(price_data['timestamp'])
            ).first()

            if existing_price:
                # Если цена существует, обновляем ее
                existing_price.price = price_data['price']
                print(f"Обновлена цена для {metal.symbol} на {price_data['timestamp']}")
            else:
                # Если цены нет, создаем новую запись
                price = MetalPrice(
                    metal_id=metal.id,
                    price=price_data['price'],
                    # Убедимся, что timestamp это datetime объект
                    timestamp=datetime.fromisoformat(price_data['timestamp']) 
                )
                db.session.add(price)
                print(f"Добавлена новая цена для {metal.symbol} на {price_data['timestamp']}")
            saved_prices_info.append(price_data)
        
        if saved_prices_info: # Только если были данные для сохранения/обновления
             db.session.commit()
             print(f"Обновление цен в БД завершено для {len(saved_prices_info)} записей.")
             # Логирование в Data Lake после успешного коммита в БД
             MetalService._log_prices_to_data_lake(saved_prices_info)
        else:
            print("Нет данных для обновления цен в БД.")

    @staticmethod
    def update_prices_from_parser():
        """Обновить цены на металлы через парсинг сайтов."""
        print("Запрос на обновление цен от парсера...")
        try:
            prices_data_from_parser = MetalParserService.get_all_current_prices()
            if prices_data_from_parser:
                print(f"Получено {len(prices_data_from_parser)} записей от парсера.")
                # Трансформируем данные, если нужно, и обновляем в БД
                # Метод update_prices ожидает 'symbol', 'price', 'timestamp' (ISO формат)
                # Вроде get_all_current_prices уже возвращает это, но проверим
                
                # Убедимся, что timestamp в правильном ISO формате и содержит дату и время
                # Парсер mfd.ru может возвращать только дату. Для консистентности, если время 00:00:00, 
                # можно оставить или добавить текущее время UTC, если это более правильно.
                # Пока что оставим как есть, предполагая, что парсер дает достаточно точный timestamp.
                MetalService.update_prices(prices_data_from_parser)
            else:
                print("Парсер не вернул данных для обновления.")
        except Exception as e:
            print(f"Ошибка при обновлении цен от парсера: {e}")
            # В реальном приложении здесь может быть более детальное логирование ошибки 
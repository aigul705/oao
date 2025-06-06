from datetime import datetime
from typing import Dict, List
import requests
from bs4 import BeautifulSoup
import os

class MetalParserService:
    METAL_SYMBOLS = {
        'GOLD': 'Золото',
        'SILVER': 'Серебро',
        'PLATINUM': 'Платина',
        'PALLADIUM': 'Палладий'
    }

    METAL_URLS = {
        'GOLD': 'https://www.investing.com/commodities/gold',
        'SILVER': 'https://www.investing.com/commodities/silver',
        'PLATINUM': 'https://www.investing.com/commodities/platinum',
        'PALLADIUM': 'https://www.investing.com/commodities/palladium',
    }

    SYMBOLS_MAP = {
        'Золото': 'GOLD',
        'Серебро': 'SILVER',
        'Платина': 'PLATINUM',
        'Палладий': 'PALLADIUM'
    }

    @staticmethod
    def get_all_current_prices() -> List[Dict]:
        url = 'https://mfd.ru/centrobank/preciousmetals/'
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
        }
        results = []
        try:
            response = requests.get(url, headers=headers)
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'html.parser')
            table = soup.find('table', class_='mfd-table')
            if not table:
                raise Exception('Не найдена таблица с классом mfd-table')
            rows = table.find_all('tr')[1:]  # пропускаем заголовок
            for row in rows:
                cols = row.find_all('td')
                if len(cols) < 5:
                    continue
                name = cols[0].text.strip()
                symbol = MetalParserService.SYMBOLS_MAP.get(name)
                if not symbol:
                    continue  # пропускаем все, что не входит в нужные металлы
                price_str = cols[1].text.strip().replace('\xa0', '').replace(',', '.').replace(' ', '')
                try:
                    price = float(price_str)
                except Exception:
                    continue
                unit = cols[2].text.strip()
                date_str = cols[4].text.strip()
                try:
                    timestamp = datetime.strptime(date_str, '%d.%m.%Y').isoformat()
                except Exception:
                    timestamp = datetime.utcnow().isoformat()
                results.append({
                    'symbol': symbol,
                    'name': name,
                    'price': price,
                    'unit': unit,
                    'timestamp': timestamp
                })
        except Exception as e:
            print('Ошибка парсинга:', str(e))
        if not results or (results and 'error' in results[0]):
            print('Ошибка парсинга mfd.ru или нет данных.')
        return results

    @staticmethod
    def get_historical_prices_from_mfd(metal_symbol: str, date_from: str, date_to: str) -> List[Dict]:
        """Парсит исторические цены для выбранного металла и периода с mfd.ru"""
        url = 'https://mfd.ru/centrobank/preciousmetals/'
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
        }
        results = []
        try:
            response = requests.get(url, headers=headers)
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'html.parser')
            table = soup.find('table', class_='mfd-table')
            if not table:
                raise Exception('Не найдена таблица с классом mfd-table')
            rows = table.find_all('tr')[1:]  # пропускаем заголовок
            symbol_map = {v: k for k, v in MetalParserService.SYMBOLS_MAP.items()}
            metal_name = symbol_map.get(metal_symbol.upper())
            if not metal_name:
                return []
            for row in rows:
                cols = row.find_all('td')
                if len(cols) < 5:
                    continue
                name = cols[0].text.strip()
                if name != metal_name:
                    continue
                price_str = cols[1].text.strip().replace('\xa0', '').replace(',', '.').replace(' ', '')
                try:
                    price = float(price_str)
                except Exception:
                    continue
                date_str = cols[4].text.strip()
                try:
                    date_obj = datetime.strptime(date_str, '%d.%m.%Y')
                except Exception:
                    continue
                if date_from <= date_obj.strftime('%Y-%m-%d') <= date_to:
                    results.append({
                        'date': date_obj.strftime('%Y-%m-%d'),
                        'price': price
                    })
        except Exception as e:
            print('Ошибка парсинга истории mfd:', str(e))
        return results 
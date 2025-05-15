from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from alpha_vantage.commodities import Commodities
from flask_caching import Cache
from app import create_app

class AlphaVantageService:
    # Metal symbols mapping
    METAL_SYMBOLS = {
        'GOLD': 'GC=F',    # Gold COMEX
        'SILVER': 'SI=F',  # Silver COMEX
        'PLATINUM': 'PL=F', # Platinum COMEX
        'PALLADIUM': 'PA=F' # Palladium COMEX
    }

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.commodities = Commodities(key=api_key)
        self.app = create_app()
        self.cache = Cache(self.app, config={
            'CACHE_TYPE': 'SimpleCache',
            'CACHE_DEFAULT_TIMEOUT': 300  # 5 minutes cache
        })

    def get_current_price(self, metal_symbol: str) -> Dict:
        """Get current price for a metal with caching."""
        cache_key = f'current_price_{metal_symbol}'
        cached_data = self.cache.get(cache_key)
        
        if cached_data:
            return cached_data

        try:
            av_symbol = self.METAL_SYMBOLS.get(metal_symbol.upper())
            if not av_symbol:
                raise ValueError(f"Unsupported metal symbol: {metal_symbol}")

            data, _ = self.commodities.get_commodities_quote(symbol=av_symbol)
            
            result = {
                'symbol': metal_symbol,
                'price': float(data['05. price']),
                'currency': 'USD',
                'timestamp': data['07. latest trading day'],
                'change': float(data['09. change']),
                'change_percent': float(data['10. change percent'].rstrip('%'))
            }
            
            # Cache the result
            self.cache.set(cache_key, result)
            return result

        except Exception as e:
            print(f"Error fetching current price for {metal_symbol}: {e}")
            raise

    def get_historical_prices(self, metal_symbol: str, 
                            start_date: datetime,
                            end_date: datetime) -> List[Dict]:
        """Get historical prices for a metal with caching."""
        cache_key = f'historical_{metal_symbol}_{start_date.date()}_{end_date.date()}'
        cached_data = self.cache.get(cache_key)
        
        if cached_data:
            return cached_data

        try:
            av_symbol = self.METAL_SYMBOLS.get(metal_symbol.upper())
            if not av_symbol:
                raise ValueError(f"Unsupported metal symbol: {metal_symbol}")

            # Get daily data
            data, _ = self.commodities.get_commodities_daily(symbol=av_symbol)
            
            # Process and filter the data
            result = []
            for date_str, values in data.items():
                date = datetime.strptime(date_str, '%Y-%m-%d')
                if start_date <= date <= end_date:
                    result.append({
                        'date': date_str,
                        'price': float(values['4. close']),
                        'open': float(values['1. open']),
                        'high': float(values['2. high']),
                        'low': float(values['3. low']),
                        'volume': int(values['5. volume'])
                    })
            
            # Sort by date
            result.sort(key=lambda x: x['date'])
            
            # Cache the result
            self.cache.set(cache_key, result)
            return result

        except Exception as e:
            print(f"Error fetching historical prices for {metal_symbol}: {e}")
            raise

    def get_all_current_prices(self) -> List[Dict]:
        """Get current prices for all metals."""
        results = []
        for metal_symbol in self.METAL_SYMBOLS.keys():
            try:
                price_data = self.get_current_price(metal_symbol)
                results.append(price_data)
            except Exception as e:
                print(f"Error fetching price for {metal_symbol}: {e}")
                continue
        return results 
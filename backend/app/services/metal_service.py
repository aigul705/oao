from datetime import datetime, timedelta
from typing import List, Dict, Optional
import statistics
from app import db
from app.models.metal import Metal, MetalPrice, MetalAnalysis
from app.services.alpha_vantage_service import MetalParserService

class MetalService:
    @staticmethod
    def get_current_prices() -> List[Dict]:
        """Get current prices for all metals."""
        metals = Metal.query.all()
        current_prices = []
        
        for metal in metals:
            # Get the latest price for each metal
            latest_price = MetalPrice.query.filter_by(metal_id=metal.id)\
                .order_by(MetalPrice.timestamp.desc())\
                .first()
            
            if latest_price:
                current_prices.append({
                    'symbol': metal.symbol,
                    'name': metal.name,
                    'price': latest_price.price,
                    'unit': metal.unit,
                    'timestamp': latest_price.timestamp.isoformat()
                })
        
        return current_prices

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
    def update_prices(prices_data: List[Dict]) -> None:
        """Update metal prices in the database."""
        for price_data in prices_data:
            metal = Metal.query.filter_by(symbol=price_data['symbol'].upper()).first()
            if not metal:
                continue

            price = MetalPrice(
                metal_id=metal.id,
                price=price_data['price'],
                timestamp=datetime.utcnow()
            )
            db.session.add(price)
        
        db.session.commit()

    @staticmethod
    def update_prices_from_parser():
        """Обновить цены на металлы через парсинг сайтов."""
        prices_data = MetalParserService.get_all_current_prices()
        for price_data in prices_data:
            if 'symbol' not in price_data or price_data['price'] is None:
                continue
            metal = Metal.query.filter_by(symbol=price_data['symbol'].upper()).first()
            if not metal:
                continue
            price = MetalPrice(
                metal_id=metal.id,
                price=price_data['price'],
                timestamp=datetime.utcnow()
            )
            db.session.add(price)
        db.session.commit() 
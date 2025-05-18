import time
from datetime import datetime
import threading
from app.services.metal_service import MetalService
from app.services.alpha_vantage_service import MetalParserService

class PriceUpdater:
    def __init__(self, app, update_interval=600):  # 600 seconds = 10 minutes
        self.app = app
        self.update_interval = update_interval
        self.running = False
        self.thread = None
        self.parser_service = MetalParserService()

    def start(self):
        """Start the price update thread."""
        if self.running:
            return

        self.running = True
        self.thread = threading.Thread(target=self._update_loop)
        self.thread.daemon = True
        self.thread.start()

    def stop(self):
        """Stop the price update thread."""
        self.running = False
        if self.thread:
            self.thread.join()

    def _update_loop(self):
        """Main update loop."""
        with self.app.app_context():
            while self.running:
                try:
                    self._fetch_and_update_prices()
                except Exception as e:
                    print(f"Error updating prices: {e}")
                time.sleep(self.update_interval)

    def _fetch_and_update_prices(self):
        """Fetch prices from web and update the database."""
        try:
            # Get current prices for all metals
            prices_data = self.parser_service.get_all_current_prices()
            # Transform the data to match our database format
            db_prices_data = []
            for price_data in prices_data:
                db_prices_data.append({
                    'symbol': price_data['symbol'],
                    'price': price_data['price'],
                    'timestamp': datetime.utcnow()
                })
            # Update prices in the database
            MetalService.update_prices(db_prices_data)
            print(f"Successfully updated prices at {datetime.utcnow()}")
        except Exception as e:
            print(f"Error fetching prices: {e}")
            raise 
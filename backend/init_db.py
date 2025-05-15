from app import create_app, db
from app.models.metal import Metal, MetalPrice, MetalAnalysis
from datetime import datetime, timedelta
import os

def init_db():
    """Initialize the database with required tables and initial data."""
    app = create_app()
    
    with app.app_context():
        # Create all tables
        db.create_all()
        
        # Check if we already have metals in the database
        if not Metal.query.first():
            print("Creating initial metal entries...")
            initial_metals = [
                Metal(symbol='GOLD', name='Gold', unit='USD/oz'),
                Metal(symbol='SILVER', name='Silver', unit='USD/oz'),
                Metal(symbol='PLATINUM', name='Platinum', unit='USD/oz'),
                Metal(symbol='PALLADIUM', name='Palladium', unit='USD/oz')
            ]
            db.session.add_all(initial_metals)
            db.session.commit()
            print("Initial metals created successfully!")
        else:
            print("Metal entries already exist.")

        # Create some initial price entries for testing
        if not MetalPrice.query.first():
            print("Creating initial price entries...")
            metals = Metal.query.all()
            now = datetime.utcnow()
            
            for metal in metals:
                # Create a price entry for each metal
                price = MetalPrice(
                    metal_id=metal.id,
                    price=1000.00 if metal.symbol == 'GOLD' else 25.00,  # Example prices
                    timestamp=now
                )
                db.session.add(price)
            
            db.session.commit()
            print("Initial price entries created successfully!")
        else:
            print("Price entries already exist.")

if __name__ == '__main__':
    # Ensure we're in the correct directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # Initialize the database
    init_db()
    print("Database initialization completed!") 
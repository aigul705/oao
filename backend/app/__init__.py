from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask_caching import Cache
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Initialize extensions
db = SQLAlchemy()
ma = Marshmallow()
cache = Cache()

# Global price updater instance
price_updater = None

def create_app():
    app = Flask(__name__)
    
    # Configure the Flask application
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///app.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Configure cache
    app.config['CACHE_TYPE'] = 'SimpleCache'
    app.config['CACHE_DEFAULT_TIMEOUT'] = 300  # 5 minutes
    
    # Initialize CORS
    CORS(app)
    
    # Initialize extensions with app
    db.init_app(app)
    ma.init_app(app)
    cache.init_app(app)
    
    # Register blueprints
    from app.routes import api_bp
    app.register_blueprint(api_bp, url_prefix='/api')
    
    # Create database tables
    with app.app_context():
        db.create_all()
        
        # Initialize metals if they don't exist
        from app.models.metal import Metal
        if not Metal.query.first():
            initial_metals = [
                Metal(symbol='GOLD', name='Gold', unit='USD/oz'),
                Metal(symbol='SILVER', name='Silver', unit='USD/oz'),
                Metal(symbol='PLATINUM', name='Platinum', unit='USD/oz'),
                Metal(symbol='PALLADIUM', name='Palladium', unit='USD/oz')
            ]
            db.session.add_all(initial_metals)
            db.session.commit()
    
    return app

def init_price_updater(app):
    """Initialize and start the price updater."""
    global price_updater
    from app.tasks.price_updater import PriceUpdater
    try:
        price_updater = PriceUpdater(app)
        price_updater.start()
    except ValueError as e:
        print(f"Warning: Price updater not started: {e}") 
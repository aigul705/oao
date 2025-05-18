from flask import Flask, send_file
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask_caching import Cache
from dotenv import load_dotenv, find_dotenv
import os
import sys

# Load environment variables
dotenv_path = find_dotenv(filename='.env', raise_error_if_not_found=False, usecwd=True)
# usecwd=True заставит его также искать в текущей рабочей директории, 
# find_dotenv обычно ищет поднимаясь вверх от места вызова или основного скрипта.
# Если мы запускаем из backend/, то .env должен найтись там.
# Если из корня, то find_dotenv может не найти backend/.env без usecwd или если он не поднимется достаточно высоко.
# Поэтому, дополнительно проверим конкретный путь, если find_dotenv не справился так, как мы хотим.

if dotenv_path:
    print(f"[DEBUG] dotenv: Found .env at: {dotenv_path}")
    load_dotenv(dotenv_path)
else:
    # Если find_dotenv не нашел (например, при запуске из корня проекта, а .env в backend/)
    # попробуем наш предыдущий "жесткий" путь.
    specific_path_to_env = os.path.join(os.path.dirname(__file__), '..', '.env')
    print(f"[DEBUG] dotenv: .env not found by find_dotenv. Trying specific path: {os.path.abspath(specific_path_to_env)}")
    if os.path.exists(specific_path_to_env):
        load_dotenv(dotenv_path=specific_path_to_env)
        dotenv_path = specific_path_to_env # Обновляем для логгирования ниже
    else:
        print(f"[DEBUG] dotenv: Specific path .env also not found at {os.path.abspath(specific_path_to_env)}.")

# Финальная проверка и логгирование значения ключа
if dotenv_path and os.path.exists(dotenv_path):
     print(f"[DEBUG] dotenv: Loaded .env from {dotenv_path}. EXCHANGE_RATE_API_KEY: {os.getenv('EXCHANGE_RATE_API_KEY')}")
else:
    print(f"[DEBUG] dotenv: .env file was NOT loaded. EXCHANGE_RATE_API_KEY: {os.getenv('EXCHANGE_RATE_API_KEY')}")

# Initialize extensions
db = SQLAlchemy()
ma = Marshmallow()
cache = Cache()

# Global price updater instance
price_updater = None

def create_app():
    # Определяем абсолютный путь к папке instance внутри backend
    # __file__ это backend/app/__init__.py
    # os.path.dirname(__file__) это backend/app/
    # os.path.join(os.path.dirname(__file__), '..', 'instance') это backend/app/../instance == backend/instance
    instance_folder_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'instance')
    
    # Создаем папку instance, если она не существует (на всякий случай)
    if not os.path.exists(instance_folder_path):
        try:
            os.makedirs(instance_folder_path)
            print(f"Created instance folder: {instance_folder_path}")
        except OSError as e:
            print(f"Error creating instance folder {instance_folder_path}: {e}", file=sys.stderr)
            # Если не удалось создать, возможно, будут проблемы дальше

    app = Flask(__name__, instance_path=instance_folder_path, instance_relative_config=True)
    
    # Configure the Flask application
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev')
    
    # Конфигурация базы данных SQLite (комментируем)
    # Теперь, когда instance_path установлен, 'sqlite:///app.db' будет автоматически искаться в instance_folder_path
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///app.db') 
    # Ниже DATABASE_URL для SQLite также может быть таким: 'sqlite:///instance/app.db'
    # Если вы хотите, чтобы файл app.db создавался в папке instance/
    
    # Конфигурация для PostgreSQL (новый)
    # ЗАМЕНИТЕ НА ВАШУ РЕАЛЬНУЮ СТРОКУ ПОДКЛЮЧЕНИЯ К POSTGRESQL
    # default_postgres_uri = 'postgresql://username:password@localhost:5432/metaldatabase'
    # app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', default_postgres_uri)
    
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

    # Route to serve the frontend
    @app.route('/')
    def serve_frontend():
        return send_file('../../frontend/index.html')
    
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
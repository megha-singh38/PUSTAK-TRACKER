from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_wtf.csrf import CSRFProtect
from flask_restful import Api
import os

db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
csrf = CSRFProtect()
api = Api()

def create_app():
    app = Flask(__name__, template_folder='frontend', static_folder='frontend/assets', static_url_path='/static')
    
    # Configure Jinja2 to handle template inheritance properly
    app.jinja_env.auto_reload = True
    app.jinja_env.cache = {}
    
    # Add datetime to Jinja2 globals
    from datetime import datetime
    app.jinja_env.globals['now'] = datetime.utcnow
    
    # Load configuration
    config_name = os.getenv('FLASK_ENV', 'development')
    if config_name == 'production':
        from .config import ProductionConfig
        app.config.from_object(ProductionConfig)
    else:
        from .config import DevelopmentConfig
        app.config.from_object(DevelopmentConfig)
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    csrf.init_app(app)
    api.init_app(app)
    
    # Register blueprints
    from .routes.web_routes import web_bp
    from .routes.api_routes import api_bp
    from .routes.db_viewer import db_viewer_bp
    from .routes.barcode_routes import barcode_bp
    
    app.register_blueprint(web_bp)
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(db_viewer_bp)
    app.register_blueprint(barcode_bp)
    
    # Create tables
    with app.app_context():
        db.create_all()
    
    return app

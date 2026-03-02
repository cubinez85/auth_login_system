from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_admin import Admin
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from config import config
import logging

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
cors = CORS()
limiter = Limiter(key_func=get_remote_address)

# Flask-Admin setup
from app.admin.views import MyAdminIndexView
admin = Admin(
    name='Auth System Admin',
    template_mode='bootstrap4',
    index_view=MyAdminIndexView()
)

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]',
    handlers=[
        logging.FileHandler('logs/app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


# app/__init__.py (фрагмент create_app)
def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # Initialize extensions with app
    db.init_app(app)
    migrate.init_app(app, db)
    cors.init_app(app)
    limiter.init_app(app)
    
    # ✅ Инициализируем admin только если не testing
    if app.config.get('TESTING', False):
        # В тестовом режиме не регистрируем admin для избежания конфликтов
        admin = None
    else:
        from flask_admin import Admin
        from app.admin.views import MyAdminIndexView
        admin = Admin(
            name='Auth System Admin',
            template_mode='bootstrap4',
            index_view=MyAdminIndexView()
        )
        admin.init_app(app)

    # Import models within app context
    with app.app_context():
        try:
            from app.models.user import User
            from app.models.permission import (
                Resource, Action, Permission,
                Role, RolePermission, UserRole, UserPermission
            )
            from app.models.token import TokenBlacklist
            logger.info("✅ Models imported successfully")
        except Exception as e:
            logger.error(f"❌ Error importing models: {e}")
            raise

    # ✅ Настраиваем admin views только если не testing
    if not app.config.get('TESTING', False):
        try:
            from app.admin.views import setup_admin
            setup_admin(admin, db)
            logger.info("✅ Admin views configured")
        except ImportError as e:
            logger.warning(f"⚠️ Could not configure admin views: {e}")

    # Register blueprints
    try:
        from app.api.auth import auth_bp
        from app.api.profile import profile_bp
        from app.api.mock_resources import mock_bp
        from app.api.admin_api import admin_api_bp
        from app.api.main_routes import main_bp

        app.register_blueprint(main_bp)
        app.register_blueprint(auth_bp)
        app.register_blueprint(profile_bp)
        app.register_blueprint(mock_bp)
        app.register_blueprint(admin_api_bp)
        
        logger.info("✅ Blueprints registered successfully")
        
    except Exception as e:
        logger.error(f"❌ Error registering blueprints: {e}")
        raise

    # Create database tables
    with app.app_context():
        try:
            db.create_all()
            logger.info("✅ Database tables created/verified")
        except Exception as e:
            logger.error(f"❌ Error creating tables: {e}")

    # Context processor for admin templates (только если не testing)
    if not app.config.get('TESTING', False):
        @app.context_processor
        def inject_counts():
            try:
                from app.admin.views import count_users, count_roles, count_permissions
                return dict(
                    count_users=count_users,
                    count_roles=count_roles,
                    count_permissions=count_permissions
                )
            except Exception as e:
                logger.error(f"Error in context processor: {e}")
                return dict(
                    count_users=lambda: 0,
                    count_roles=lambda: 0,
                    count_permissions=lambda: 0
                )

    # Error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return {'error': 'Not found', 'message': str(error)}, 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        logger.error(f"Internal server error: {error}")
        return {'error': 'Internal server error'}, 500

    @app.errorhandler(429)
    def ratelimit_handler(e):
        return {'error': 'Rate limit exceeded', 'message': str(e.description)}, 429

    logger.info(f"🚀 Application created with config: {config_name}")
    return app

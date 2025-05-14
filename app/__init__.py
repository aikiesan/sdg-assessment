import os
from datetime import datetime, timezone
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_mail import Mail
from flask_wtf.csrf import CSRFProtect
from config import Config, DevelopmentConfig, TestingConfig, ProductionConfig, config
from sqlalchemy import text

# --- Instantiate Extensions ---
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
mail = Mail()
csrf = CSRFProtect()

@login_manager.user_loader
def load_user(user_id):
    """Load user by ID."""
    from app.models.user import User
    return db.session.get(User, int(user_id))

def create_app(config_name=None):
    import logging
    from datetime import datetime
    
    app = Flask(__name__, instance_relative_config=True)
    
    # Add format_date filter for templates
    def format_datetime(value, format='%b %d, %Y'):
        if value is None:
            return ""
        return value.strftime(format)
    
    app.jinja_env.filters['format_date'] = format_datetime


    if config_name is None:
        config_name = os.environ.get('FLASK_CONFIG', 'default')

    if isinstance(config_name, str):
        config_class = config.get(config_name, Config)
    else:
        config_class = config_name
    app.config.from_object(config_class)


    import logging
    if app.config.get('TESTING'):
        print(f"!!! Setting Logger Level to INFO for Testing !!!")
        log_level = logging.INFO


    else:
        log_level = logging.INFO # Or your default production level

    if not app.logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s [%(funcName)s:%(lineno)d]')
        handler.setFormatter(formatter)
        app.logger.addHandler(handler)
        app.logger.propagate = False

    app.logger.setLevel(log_level)


    app.logger.critical("Flask App Logger Initialized with Level: %s", app.logger.getEffectiveLevel())


    import click
    from flask.cli import with_appcontext
    from app.utils.db import get_db
    
    @click.command('update-schema')
    @with_appcontext
    def update_schema_command():
        """Update database schema for new features."""
        try:
            # Check if draft_data column exists in assessments table
            result = db.session.execute(text("PRAGMA table_info(assessments)"))
            columns = [row[1] for row in result.fetchall()]  # Column names are in index 1
            has_draft_data = 'draft_data' in columns

            if not has_draft_data:
                # Add draft_data column
                db.session.execute(text("""
                    ALTER TABLE assessments 
                    ADD COLUMN draft_data TEXT
                """))
                print("Added draft_data column to assessments table")

            # Check if response_text and notes columns exist in sdg_scores table
            result = db.session.execute(text("PRAGMA table_info(sdg_scores)"))
            columns = [row[1] for row in result.fetchall()]  # Column names are in index 1
            has_response_text = 'response_text' in columns

            if not has_response_text:
                # Add response_text and notes columns
                db.session.execute(text("""
                    ALTER TABLE sdg_scores 
                    ADD COLUMN response_text TEXT,
                    ADD COLUMN notes TEXT
                """))
                print("Added response_text and notes columns to sdg_scores table")

                # Copy data from score_text to response_text
                db.session.execute(text("""
                    UPDATE sdg_scores 
                    SET response_text = score_text 
                    WHERE score_text IS NOT NULL
                """))
                print("Copied data from score_text to response_text")

            db.session.commit()
            print("Schema update completed successfully")
        except Exception as e:
            db.session.rollback()
            print(f"Error updating schema: {e}")
            raise

    app.cli.add_command(update_schema_command)


    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', app.config.get('SECRET_KEY', 'your-default-secret-key'))
    if 'DATABASE_URI' in os.environ:
        app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URI']
    
    # --- Initialize Extensions ---
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)
    csrf.init_app(app)

    # Register filters (if filters.py exists)
    try:
        from . import filters
        filters.register_filters(app)
    except ImportError:
        pass


    from . import models


    def format_date(value, format='%Y-%m-%d'):
        """Format a date using specified format."""
        if isinstance(value, str):
            try:
                value = datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
            except ValueError:
                return value
        return value.strftime(format) if value else ""
    app.jinja_env.filters['format_date'] = format_date

    @app.context_processor
    def inject_now():
        return {'now': datetime.now(timezone.utc)}


    @app.teardown_appcontext
    def shutdown_session(exception=None):
        db.session.remove()


    if hasattr(app, 'before_serving'):
        @app.before_serving
        def init_db():
            from sqlalchemy import text
            with db.engine.connect() as connection:
                connection.execute(text('''
                    CREATE VIEW IF NOT EXISTS sdg_questions_view AS
                    SELECT q.id, q.text, q.type, q.sdg_id as primary_sdg_id, g.number as sdg_number, g.name as sdg_name, q.max_score
                    FROM sdg_questions q
                    JOIN sdg_goals g ON q.sdg_id = g.id
                '''))
    else:

        from sqlalchemy import text
        with app.app_context():
            with db.engine.connect() as connection:
                connection.execute(text('''
                    CREATE VIEW IF NOT EXISTS sdg_questions_view AS
                    SELECT q.id, q.text, q.type, q.sdg_id as primary_sdg_id, g.number as sdg_number, g.name as sdg_name, q.max_score
                    FROM sdg_questions q
                    JOIN sdg_goals g ON q.sdg_id = g.id
                '''))


    # Register blueprints
    from app.routes import main_bp, auth_bp, projects_bp, assessments_bp, questionnaire_bp, api_bp, dashboard_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(projects_bp, url_prefix='/projects')
    app.register_blueprint(assessments_bp, url_prefix='/assessments')
    app.register_blueprint(questionnaire_bp, url_prefix='/questionnaire')
    app.register_blueprint(api_bp, url_prefix='/api')

    # Register error handlers
    from app.utils.errors import register_error_handlers
    register_error_handlers(app)

    # Register CLI commands
    from app.cli import register_cli_commands
    register_cli_commands(app)

    return app

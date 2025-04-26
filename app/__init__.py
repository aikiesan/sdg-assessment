import os
from datetime import datetime, timezone
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_mail import Mail  # <-- ADD THIS LINE
import os
from config import Config, DevelopmentConfig, TestingConfig, ProductionConfig, config

# --- Instantiate Extensions ---
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
mail = Mail()  # <-- ADD THIS LINE

@login_manager.user_loader
def load_user(user_id):
    from app.models.user import User
    return User.query.get(int(user_id))

def create_app(config_name=None):
    import logging
    app = Flask(__name__, instance_relative_config=True)


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
        """Add or modify columns in assessments and sdg_scores tables as needed for new model fields."""
        conn = get_db()

        columns = [col['name'] for col in conn.execute("PRAGMA table_info(assessments)").fetchall()]
        if 'draft_data' not in columns:
            conn.execute('ALTER TABLE assessments ADD COLUMN draft_data TEXT')
            conn.commit()
            click.echo('Added draft_data column to assessments table')


        sdg_columns = [col['name'] for col in conn.execute("PRAGMA table_info(sdg_scores)").fetchall()]
        if 'response_text' not in sdg_columns:
            conn.execute('ALTER TABLE sdg_scores ADD COLUMN response_text TEXT')
            conn.commit()
            click.echo('Added response_text column to sdg_scores table')
        if 'notes' not in sdg_columns:
            conn.execute('ALTER TABLE sdg_scores ADD COLUMN notes TEXT')
            conn.commit()
            click.echo('Added notes column to sdg_scores table')
        if 'final_score' in sdg_columns and 'total_score' not in sdg_columns:
            conn.execute('ALTER TABLE sdg_scores ADD COLUMN total_score FLOAT')
            conn.execute('UPDATE sdg_scores SET total_score = final_score')
            conn.commit()
            click.echo('Copied final_score data to total_score column in sdg_scores table')
            conn.execute('ALTER TABLE sdg_scores DROP COLUMN final_score')
            conn.commit()
            click.echo('Dropped final_score column from sdg_scores table')

    app.cli.add_command(update_schema_command)


    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', app.config.get('SECRET_KEY', 'your-default-secret-key'))
    if 'DATABASE_URI' in os.environ:
        app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URI']
    
    # --- Initialize Extensions ---
    db.init_app(app)
    login_manager.init_app(app)
    # login_manager.login_view = 'auth.login' # Already set globally
    migrate.init_app(app, db)
    mail.init_app(app)  # <-- ADD THIS LINE TO INITIALIZE MAIL

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


    from app.routes.main import main_bp
    from app.routes.auth import auth_bp
    from app.routes.projects import projects_bp
    from app.routes.assessments import assessments_bp
    from app.routes.questionnaire import questionnaire_bp
    from app.routes.dashboard import dashboard_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(projects_bp, url_prefix='/projects')
    app.register_blueprint(assessments_bp, url_prefix='/assessments')
    app.register_blueprint(questionnaire_bp, url_prefix='/questionnaire')
    app.register_blueprint(dashboard_bp, url_prefix='/dashboard')


    from app.routes.assessments_cli import register_cli_commands
    register_cli_commands(app)


    from app.routes.goals_cli import populate_goals_command
    app.cli.add_command(populate_goals_command)
    
    return app

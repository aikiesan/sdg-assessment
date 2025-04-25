# tests/conftest.py
import pytest
import os
from app import create_app, db
from app.models.user import User
from app.models.project import Project
from app.models.assessment import Assessment
from config import TestingConfig
from werkzeug.security import generate_password_hash

from app.utils.db_utils import populate_goals, populate_questions

@pytest.fixture(scope='session') # Keep app session-scoped
def app():
    """Create and configure a new app instance for tests."""
    print("Creating Flask app for test session...")
    app = create_app(TestingConfig)
    # No need to push context here usually
    yield app

# --- Make _db session-scoped AGAIN ---
@pytest.fixture(scope='session')
def _db(app): # Depends on session-scoped app
    """Session-wide database setup."""
    print("Setting up database for test session...")
    with app.app_context(): # Ensure DB operations happen within context
        db.create_all()
        print("  -> DB Tables created for session.")
        yield db # Provide db for population fixture and function sessions
        print("  <- Dropping database tables after session.")
        db.drop_all()
        # ... (DB file deletion) ...

# --- Keep populate_db session-scoped ---
@pytest.fixture(scope='session', autouse=True)
def populate_db(_db, app): # Depends on session-scoped app and _db
     """Populates the database with static data ONCE per session."""
     print("Populating static DB data for session...")
     with app.app_context():
         print("   Populating goals via direct call...")
         success_goals = populate_goals() # Assumes this uses db.session internally now
         assert success_goals is True, "populate_goals function failed"

         print("   Populating questions via direct call...")
         success_questions = populate_questions() # Assumes this uses db.session internally now
         assert success_questions is True, "populate_questions function failed"

     print("Static DB data populated.")

# Fixture for running CLI commands within tests
@pytest.fixture(scope='function')
def runner(app):
    """A test runner for the app's Click commands."""
    return app.test_cli_runner()

# --- Session-scoped DB fixture ---
@pytest.fixture(scope='function')
def session(_db):
    """Provides the db.session object scoped to a test function."""
    print("   -> Providing db.session for test function.")
    yield _db.session  # Provide the regular session managed by Flask-SQLAlchemy
    # Cleanup happens in _db fixture teardown (drop_all)
    # No explicit rollback/remove here; handled by _db

# Fixture for creating a test user
@pytest.fixture(scope='function')
def test_user(session):
    """Create a user for testing (flush only)."""
    print("     -> Creating test user object...")
    user = User(
        name='Test User',
        email=f'test_{os.urandom(4).hex()}@example.com',
        password_hash=generate_password_hash('password')
    )
    session.add(user)
    session.commit()
    print(f"     <- Test user created and committed (ID: {user.id}, Email: {user.email}).")
    return user

# Fixture for creating another user
@pytest.fixture(scope='function')
def other_user(session):
     print("     -> Creating other user object...")
     user = User(
         name='Other User',
         email=f'other_{os.urandom(4).hex()}@example.com',
         password_hash=generate_password_hash('password') # Corrected
     )
     session.add(user)
     session.flush()
     print(f"     <- Other user object flushed (ID: {user.id}).")
     return user

# --- Fixture to populate data ONCE per session ---
@pytest.fixture(scope='session', autouse=True)
def populate_db(_db, app):
     """Populates the database with static data ONCE per session."""
     print("Populating static DB data for session...")
     with app.app_context():
         # --- Option 2: Call functions directly (Preferred) ---
         # Ensure functions are imported from correct location (db_utils)
         print("   Populating goals via direct call...")
         success_goals = populate_goals() # Calls imported function
         assert success_goals is True, "populate_goals function failed"

         print("   Populating questions via direct call...")
         success_questions = populate_questions() # Calls imported function
         assert success_questions is True, "populate_questions function failed"
         # ------------------------------------------------------------------------

         # --- Option 1: Use CLI Runner (Remove if using Option 2) ---
         # runner = app.test_cli_runner()
         # print("   Populating test DB: sdg_goals...")
         # result_goals = runner.invoke(args=['populate-goals'])
         # print(result_goals.output)
         # assert 'CLI: sdg_goals table populated successfully' in result_goals.output

         # print("   Populating test DB: sdg_questions...")
         # result_questions = runner.invoke(args=['populate-questions'])
         # print(result_questions.output)
         # assert 'CLI: sdg_questions table populated successfully' in result_questions.output
         # -------------------------------------------------------------
     print("Static DB data populated.")

# --- ADD THIS FIXTURE BACK ---
@pytest.fixture(scope='function')
def test_project(session, test_user): # Depends on session and test_user
    """Create a project owned by the test user."""
    print("     -> Creating test project...")
    project = Project(name='Assessment Test Project', user_id=test_user.id, project_type='commercial', location='Test Location Fixture')
    session.add(project)
    session.flush() # Use flush instead of commit
    print(f"     <- Test project flushed (ID: {project.id} - pending rollback).")
    return project
# --- END ADD ---

# Helper class for authentication actions
class AuthActions:
    def __init__(self, client):
        self._client = client

    def login(self, email='test@example.com', password='password'):
        return self._client.post('/auth/login', data=dict(
            email=email,
            password=password
        ), follow_redirects=True)

    def logout(self):
        return self._client.get('/auth/logout', follow_redirects=True)

# Fixture providing the AuthActions helper
@pytest.fixture(scope='function')
def auth(client): # Depends on the implicit 'client' from pytest-flask
    """Fixture to perform login/logout actions."""
    return AuthActions(client)

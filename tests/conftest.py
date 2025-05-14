# tests/conftest.py
import pytest
import os
import uuid
from app import create_app, db as _db  # Use _db to avoid conflict with fixture name
from app.models.user import User
from app.models.project import Project
from app.models.assessment import Assessment
from app.models.sdg import SdgQuestion, SdgGoal  # For verification
from config import TestingConfig
from werkzeug.security import generate_password_hash
from app.utils.db_utils import populate_goals, populate_questions
from datetime import datetime

@pytest.fixture(scope='session')
def app():
    """Session-wide test Flask application."""
    print("\n--- Creating Flask app for test session ---")
    app = create_app(TestingConfig)
    print(f"!!! Using Testing Config: {app.config.get('SQLALCHEMY_DATABASE_URI', 'URI not set')} !!!")
    app_context = app.app_context()
    app_context.push()
    yield app
    app_context.pop()
    print("--- Flask app context popped ---")

@pytest.fixture(scope='session')
def db(app):
    """Session-wide test database setup and static data population."""
    print("\n--- Setting up session database ---")
    with app.app_context():
        _db.app = app
        _db.create_all()
        print("--- Tables created ---")

        print("--- Attempting to populate static SDG data ---")
        try:
            print("   Populating goals...")
            populate_goals() # Assumes this adds to _db.session
            print("   -> Goals added to session.")

            print("   Populating questions...")
            populate_questions() # Assumes this adds to _db.session
            print("   -> Questions added to session.")

            # --- Verification BEFORE commit ---
            goal_count_before = _db.session.query(SdgGoal).count()
            q_count_before = _db.session.query(SdgQuestion).count()
            print(f"--- Verification (Before Commit): Found {goal_count_before} goals and {q_count_before} questions in session. ---")

            # --- Single Commit ---
            _db.session.commit() # Commit all populated data together
            print("--- Static data committed. ---")

            # --- Verification AFTER commit ---
            goal_count_after = _db.session.query(SdgGoal).count()
            q_count_after = _db.session.query(SdgQuestion).count()
            print(f"--- Verification (After Commit): Found {goal_count_after} goals and {q_count_after} questions in DB query. ---")

            if goal_count_after == 0 or q_count_after == 0:
                 pytest.fail("Static SDG data population resulted in 0 essential records after commit.")
            print("--- Static data population successful ---")

        except Exception as e:
            print(f"--- ERROR during static data population: {e} ---")
            _db.session.rollback()
            pytest.fail(f"Static data population failed: {e}", pytrace=False)

    yield _db

    # Teardown
    print("\n--- Tearing down session database ---")
    with app.app_context():
         _db.drop_all()
    print("--- Database dropped ---")

@pytest.fixture(scope='function')
def session(app, db):  # Depends on app and session-scoped db
    """
    Function-scoped session fixture using nested transactions.
    Relies on the standard Flask-SQLAlchemy `db.session`.
    """
    with app.app_context():  # Ensures db.session is accessed within the correct context
        print("--- Setting up function-scoped session (nested transaction) ---")
        # Start a nested transaction (uses SAVEPOINT)
        db.session.begin_nested()

        # Optional verification
        q_count_func = db.session.query(SdgQuestion).count()
        print(f"--- Check at start of function session: {q_count_func} SdgQuestions ---")
        if q_count_func == 0:
            # This indicates an issue if static data wasn't available here
            print("!!! WARNING: 0 SdgQuestions found at start of function scope !!!")

        # Yield the standard Flask-SQLAlchemy session object
        # Tests will use this session for their operations.
        yield db.session

        # Teardown for function scope (after test function runs)
        # Rollback the nested transaction, undoing changes made in the test
        db.session.rollback()
        print("--- Function session (nested transaction) rolled back ---")

@pytest.fixture(scope='function')
def client(app, session):  # Inject function-scoped session to ensure client uses same context if needed
    """Provides a test client."""
    return app.test_client()

@pytest.fixture(scope='function')
def test_user(session):  # Depends on function-scoped session
    """Creates a test user within the function transaction."""
    print("   -> Creating test user object...")
    user = User(
        name='Test User',
        email=f"test_{uuid.uuid4().hex[:8]}@example.com",
        password_hash=generate_password_hash('password')
    )
    session.add(user)
    session.flush()  # Use flush to get ID if needed, commit isn't necessary due to rollback
    print(f"   <- Test user flushed (ID: {user.id if user.id else 'N/A'} - pending rollback).")
    return user

@pytest.fixture(scope='function')
def other_user(session):
    """Creates another test user within the function transaction."""
    print("   -> Creating other user object...")
    user = User(
        name='Other User',
        email=f"other_{uuid.uuid4().hex[:8]}@example.com",
        password_hash=generate_password_hash('password')
    )
    session.add(user)
    session.flush()
    print(f"   <- Other user flushed (ID: {user.id if user.id else 'N/A'} - pending rollback).")
    return user

@pytest.fixture(scope='function')
def test_project(session, test_user):  # Depends on function-scoped session
    """Creates a test project within the function transaction."""
    print("   -> Creating test project...")
    project = Project(
        name="Test Project Fixture",
        user_id=test_user.id,
        project_type='commercial',
        location='Test Location Fixture',
        description='A test project fixture description.',
        start_date=datetime(2024, 1, 1),
        end_date=datetime(2024, 12, 31),
        budget=50000.0,
        sector='Technology'
    )
    session.add(project)
    session.flush()
    print(f"   <- Test project flushed (ID: {project.id} - pending rollback).")
    return project

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

@pytest.fixture(scope='function')
def auth(client):  # Depends on the function-scoped client
    """Fixture to perform login/logout actions."""
    return AuthActions(client)

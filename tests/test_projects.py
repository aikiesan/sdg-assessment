# tests/test_projects.py
import pytest
from app.models.project import Project
from app.models.user import User
from app import db
import os
from werkzeug.security import generate_password_hash
from flask import url_for, session as flask_session

def test_projects_page_unauthenticated(client):
    """Accessing projects requires login and should redirect."""
    response = client.get('/projects/')
    # --- CORRECT ASSERTIONS ---
    assert response.status_code == 302
    assert '/auth/login' in response.headers['Location']
    # --- END CORRECTION ---

def test_projects_page_authenticated(client, auth, test_user):
    """Accessing projects works when logged in."""
    # Login using the specific user created for this test
    auth.login(email=test_user.email)
    response = client.get('/projects/')
    assert response.status_code == 200
    # Update this assertion to match your actual template content
    assert b'My Projects' in response.data

def test_create_project(client, auth, test_user, session):
    """Test creating a new project."""
    # Login using the specific user created for this test
    auth.login(email=test_user.email)
    response = client.post('/projects/new', data=dict(
        name='My Test Project',
        description='A project created during testing.',
        project_type='residential',
        location='Test Location',
        size_sqm='1000'
    ), follow_redirects=True)

    assert response.status_code == 200
    assert b'Project created successfully' in response.data
    assert b'My Test Project' in response.data

    # Check database
    project = Project.query.filter_by(name='My Test Project', user_id=test_user.id).first()
    assert project is not None
    assert project.location == 'Test Location'


@pytest.fixture(scope='function')
def other_user(session):
    print("     -> Creating other user object...")
    user = User(
        name='Other User',
        email=f'other_{os.urandom(4).hex()}@example.com',
        password_hash=generate_password_hash('password')
    )
    session.add(user)
    session.flush()
    print(f"     <- Other user object flushed (ID: {user.id}).")
    return user


from flask import url_for

def test_edit_project_unauthorized(client, auth, other_user, test_project):
    """Test that a user cannot edit another user's project."""
    auth.login(email=other_user.email)
    edit_url = f'/projects/{test_project.id}/edit'
    print(f"Attempting GET on: {edit_url} as other_user")

    response_get = client.get(edit_url, follow_redirects=False)
    print(f"GET response status: {response_get.status_code}")
    # --- RE-APPLY ASSERTION FIX ---
    assert response_get.status_code == 302 # Expect redirect
    # Check redirect location
    assert url_for('projects.index') in response_get.headers.get('Location', '') or \
           url_for('main.index') in response_get.headers.get('Location', '')
    # --- END FIX ---

    print(f"Attempting POST on: {edit_url} as other_user")
    response_post = client.post(edit_url, data={'name': 'Hacked Name'}, follow_redirects=False)
    print(f"POST response status: {response_post.status_code}")
    # --- RE-APPLY ASSERTION FIX ---
    assert response_post.status_code == 302 # Expect redirect
    # Check redirect location
    assert url_for('projects.index') in response_post.headers.get('Location', '') or \
           url_for('main.index') in response_post.headers.get('Location', '')
    # --- END FIX ---


def test_view_nonexistent_project(client, auth, test_user):
    """Test viewing a project that doesn't exist."""
    auth.login(email=test_user.email)
    response = client.get('/projects/99999') # Use an ID that won't exist
    assert response.status_code == 404 # Check for Not Found


def test_create_project_invalid_data(client, auth, test_user):
    """Test creating a project with missing/invalid data."""
    auth.login(email=test_user.email)
    # Example: Missing name
    response = client.post('/projects/new', data=dict(
        description='Missing name',
        project_type='residential',
    ), follow_redirects=True)
    assert response.status_code == 200 # Usually re-renders the form
    assert b'Project name is required' in response.data # Check for validation error message


def test_edit_project_get(client, auth, test_user, test_project):
    """Test loading the edit project page."""
    auth.login(email=test_user.email)
    response = client.get(f'/projects/{test_project.id}/edit')
    assert response.status_code == 200
    # Check that the form is pre-filled with existing project data
    assert bytes(test_project.name, 'utf-8') in response.data
    if test_project.location:
        assert bytes(test_project.location, 'utf-8') in response.data


def test_edit_project_post(client, auth, test_user, test_project, session):
    """Test submitting changes to a project."""
    auth.login(email=test_user.email)
    edit_url = f'/projects/{test_project.id}/edit'
    new_data = {
        'name': 'Updated Project Name',
        'description': 'Updated description.',
        'project_type': 'commercial',
        'location': 'New Location',
        'size_sqm': '1500'
    }
    response = client.post(edit_url, data=new_data, follow_redirects=True)
    assert response.status_code == 200
    assert b'Project updated successfully' in response.data
    assert b'Updated Project Name' in response.data

    # Check database
    updated_project = session.get(Project, test_project.id)
    assert updated_project.name == 'Updated Project Name'
    assert updated_project.location == 'New Location'
    assert updated_project.size_sqm == 1500.0


def test_delete_project(client, auth, test_user, test_project, session):
    """Test deleting a project."""
    auth.login(email=test_user.email)
    project_id_to_delete = test_project.id
    delete_url = f'/projects/{project_id_to_delete}/delete'

    response_post = client.post(delete_url) # No redirect follow needed if checking session

    # Check redirect
    assert response_post.status_code == 302
    assert url_for('projects.index') in response_post.headers['Location']

    # Check flash message in session
    with client.session_transaction() as flask_sess:
        assert '_flashes' in flask_sess
        flashed_messages = dict(flask_sess['_flashes'])
        print(f"Flashes after delete: {flashed_messages}")
        assert flashed_messages.get('success') == 'Project deleted successfully'

    # Check database
    deleted_project = session.get(Project, project_id_to_delete)
    assert deleted_project is None
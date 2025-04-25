# tests/test_projects.py
import pytest
from app.models.project import Project
from app import db

def test_projects_page_unauthenticated(client):
    """Accessing projects requires login."""
    response = client.get('/projects/')
    assert response.status_code == 302 # Redirect to login

def test_projects_page_authenticated(client, auth, test_user):
    """Accessing projects works when logged in."""
    auth.login()
    response = client.get('/projects/')
    assert response.status_code == 200
    assert b'Your Projects' in response.data # Check content

def test_create_project(client, auth, test_user, session):
    """Test creating a new project."""
    auth.login()
    response = client.post('/projects/new', data=dict(
        name='My Test Project',
        description='A project created during testing.',
        project_type='residential',
        location='Test Location',
        size_sqm='1000'
    ), follow_redirects=True)

    assert response.status_code == 200
    assert b'Project created successfully' in response.data # Check flash message
    assert b'My Test Project' in response.data # Check if project name appears on index

    # Check database
    project = Project.query.filter_by(name='My Test Project').first()
    assert project is not None
    assert project.user_id == test_user.id
    assert project.location == 'Test Location'
# tests/test_auth.py
import pytest
from flask import session
from app.models.user import User

def test_login_logout(auth, client, test_user):
    """Test login and logout using the auth fixture."""
    # Test login
    response = auth.login()
    assert response.status_code == 200
    assert b"Logout" in response.data # Check for logout link
    assert b"Login Required" not in response.data

    # Check session variable
    with client: # Use client as context manager to maintain session
        # Check accessing a protected route (e.g., projects index)
        response_projects = client.get('/projects/')
        assert response_projects.status_code == 200
        assert b'Your Projects' in response_projects.data # Or some text from projects page

        # Test logout
        response_logout = auth.logout()
        assert response_logout.status_code == 200
        assert b"You have been logged out" in response_logout.data
        assert b"Login" in response_logout.data # Check for login link

        # Check accessing protected route after logout
        response_projects_after_logout = client.get('/projects/')
        assert response_projects_after_logout.status_code == 302 # Should redirect to login

def test_login_invalid_password(auth, client, test_user):
    """Test login with incorrect password."""
    response = auth.login(password='wrongpassword')
    assert response.status_code == 200
    assert b'Invalid email or password' in response.data
    assert b'Logout' not in response.data
# tests/test_basic.py
import pytest

def test_index_page(client):
    """Test that the index page loads."""
    response = client.get('/')
    assert response.status_code == 200
    assert b"Welcome to the SDG Assessment Tool" in response.data # Check for some unique text

def test_config(app):
    """Test that the testing config is loaded."""
    assert app.config['TESTING'] is True
    assert not app.config['WTF_CSRF_ENABLED']
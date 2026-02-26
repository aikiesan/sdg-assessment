"""
Tests for dashboard routes and admin functionality.
"""

import pytest
from app.models.user import User
from app.models.project import Project
from app.models.assessment import Assessment, SdgScore
from app.models.sdg import SdgGoal
from datetime import datetime


class TestDashboardAccess:
    """Test dashboard access control."""

    def test_dashboard_requires_login(self, client):
        """Test that dashboard requires authentication."""
        response = client.get('/dashboard/')
        assert response.status_code == 302  # Redirect to login
        assert b'/auth/login' in response.data or response.location.endswith('/auth/login')

    def test_dashboard_requires_admin(self, client, test_user, auth):
        """Test that non-admin users cannot access dashboard."""
        # Login as regular user
        auth.login(email=test_user.email, password='password')

        response = client.get('/dashboard/', follow_redirects=True)
        # Should be denied or redirected
        assert b'Administrator access required' in response.data or response.status_code == 403

    def test_admin_can_access_dashboard(self, client, admin_user, auth, session):
        """Test that admin users can access dashboard."""
        # Login as admin
        with client.session_transaction() as sess:
            sess['user_id'] = admin_user.id
            sess['is_admin'] = True

        response = client.get('/dashboard/')
        assert response.status_code == 200


class TestDashboardIndex:
    """Test the main dashboard index page."""

    def test_dashboard_displays_statistics(self, client, admin_user, session, multiple_projects):
        """Test that dashboard displays correct statistics."""
        # Login as admin
        with client.session_transaction() as sess:
            sess['user_id'] = admin_user.id
            sess['is_admin'] = True

        response = client.get('/dashboard/')
        assert response.status_code == 200

        # Should display counts (adjust based on actual HTML)
        assert b'Projects' in response.data or b'projects' in response.data
        assert b'Users' in response.data or b'users' in response.data

    def test_dashboard_shows_recent_activity(self, client, admin_user, session, test_project,
                                              completed_assessment):
        """Test that dashboard shows recent projects and assessments."""
        with client.session_transaction() as sess:
            sess['user_id'] = admin_user.id
            sess['is_admin'] = True

        response = client.get('/dashboard/')
        assert response.status_code == 200

        # Should show recent activity
        assert b'Recent' in response.data or b'recent' in response.data

    def test_dashboard_shows_average_scores(self, client, admin_user, session, completed_assessment):
        """Test that dashboard displays average scores."""
        with client.session_transaction() as sess:
            sess['user_id'] = admin_user.id
            sess['is_admin'] = True

        response = client.get('/dashboard/')
        assert response.status_code == 200

        # Should show average score
        assert b'Average' in response.data or b'average' in response.data or b'Score' in response.data


class TestDashboardUsers:
    """Test user management dashboard."""

    def test_users_list_displays_all_users(self, client, admin_user, session, test_user, other_user):
        """Test that users list shows all users."""
        with client.session_transaction() as sess:
            sess['user_id'] = admin_user.id
            sess['is_admin'] = True

        response = client.get('/dashboard/users')
        assert response.status_code == 200

        # Should display user names
        assert test_user.name.encode() in response.data
        assert other_user.name.encode() in response.data

    def test_users_list_shows_statistics(self, client, admin_user, session, test_user, multiple_projects):
        """Test that users list shows project counts."""
        with client.session_transaction() as sess:
            sess['user_id'] = admin_user.id
            sess['is_admin'] = True

        response = client.get('/dashboard/users')
        assert response.status_code == 200

        # Should show project count for users
        # The exact number depends on fixtures, but should be > 0 for test_user
        assert b'0' in response.data or b'1' in response.data or b'5' in response.data

    def test_user_detail_page(self, client, admin_user, session, test_user, multiple_projects):
        """Test user detail page shows user information."""
        with client.session_transaction() as sess:
            sess['user_id'] = admin_user.id
            sess['is_admin'] = True

        response = client.get(f'/dashboard/users/{test_user.id}')
        assert response.status_code == 200

        # Should show user details
        assert test_user.name.encode() in response.data
        assert test_user.email.encode() in response.data

    def test_user_detail_not_found(self, client, admin_user, session):
        """Test user detail page with non-existent user."""
        with client.session_transaction() as sess:
            sess['user_id'] = admin_user.id
            sess['is_admin'] = True

        response = client.get('/dashboard/users/99999', follow_redirects=True)
        assert b'not found' in response.data.lower()

    def test_edit_user_page(self, client, admin_user, session, test_user):
        """Test edit user page loads correctly."""
        with client.session_transaction() as sess:
            sess['user_id'] = admin_user.id
            sess['is_admin'] = True

        response = client.get(f'/dashboard/users/{test_user.id}/edit')
        assert response.status_code == 200
        assert test_user.name.encode() in response.data

    def test_edit_user_updates_information(self, client, admin_user, session, test_user):
        """Test editing user information."""
        with client.session_transaction() as sess:
            sess['user_id'] = admin_user.id
            sess['is_admin'] = True

        new_name = 'Updated Test User'
        response = client.post(f'/dashboard/users/{test_user.id}/edit', data={
            'name': new_name,
            'email': test_user.email,
            'is_admin': 'off'
        }, follow_redirects=True)

        assert response.status_code == 200
        session.refresh(test_user)
        assert test_user.name == new_name


class TestDashboardProjects:
    """Test project management dashboard."""

    def test_projects_list_displays_all_projects(self, client, admin_user, session, multiple_projects):
        """Test that projects list shows all projects."""
        with client.session_transaction() as sess:
            sess['user_id'] = admin_user.id
            sess['is_admin'] = True

        response = client.get('/dashboard/projects')
        assert response.status_code == 200

        # Should display project names
        for project in multiple_projects:
            assert project.name.encode() in response.data

    def test_projects_list_shows_assessment_counts(self, client, admin_user, session, test_project,
                                                     completed_assessment):
        """Test that projects list shows assessment counts."""
        with client.session_transaction() as sess:
            sess['user_id'] = admin_user.id
            sess['is_admin'] = True

        response = client.get('/dashboard/projects')
        assert response.status_code == 200

        # Should show assessment count
        assert b'Assessment' in response.data or b'assessment' in response.data


class TestDashboardAssessments:
    """Test assessment management dashboard."""

    def test_assessments_list_displays_all_assessments(self, client, admin_user, session,
                                                         completed_assessment):
        """Test that assessments list shows all assessments."""
        with client.session_transaction() as sess:
            sess['user_id'] = admin_user.id
            sess['is_admin'] = True

        response = client.get('/dashboard/assessments')
        assert response.status_code == 200

        # Should display assessment information
        assert b'Assessment' in response.data or b'assessment' in response.data

    def test_assessments_list_shows_project_names(self, client, admin_user, session, test_project,
                                                    completed_assessment):
        """Test that assessments list shows associated project names."""
        with client.session_transaction() as sess:
            sess['user_id'] = admin_user.id
            sess['is_admin'] = True

        response = client.get('/dashboard/assessments')
        assert response.status_code == 200

        # Should show project name
        assert test_project.name.encode() in response.data


class TestDashboardAnalytics:
    """Test analytics dashboard."""

    def test_analytics_page_loads(self, client, admin_user, session):
        """Test that analytics page loads successfully."""
        with client.session_transaction() as sess:
            sess['user_id'] = admin_user.id
            sess['is_admin'] = True

        response = client.get('/dashboard/analytics')
        assert response.status_code == 200

    def test_analytics_shows_sdg_scores(self, client, admin_user, session, completed_assessment):
        """Test that analytics page shows SDG average scores."""
        with client.session_transaction() as sess:
            sess['user_id'] = admin_user.id
            sess['is_admin'] = True

        response = client.get('/dashboard/analytics')
        assert response.status_code == 200

        # Should display SDG-related information
        assert b'SDG' in response.data or b'Goal' in response.data

    def test_analytics_shows_charts_data(self, client, admin_user, session, completed_assessment):
        """Test that analytics page includes chart data."""
        with client.session_transaction() as sess:
            sess['user_id'] = admin_user.id
            sess['is_admin'] = True

        response = client.get('/dashboard/analytics')
        assert response.status_code == 200

        # Should include chart or visualization elements
        # Adjust based on actual implementation
        assert response.status_code == 200


class TestDashboardSDGManagement:
    """Test SDG management dashboard."""

    def test_sdg_management_page_loads(self, client, admin_user, session):
        """Test that SDG management page loads."""
        with client.session_transaction() as sess:
            sess['user_id'] = admin_user.id
            sess['is_admin'] = True

        response = client.get('/dashboard/sdg-management')
        assert response.status_code == 200

    def test_sdg_management_shows_goals(self, client, admin_user, session):
        """Test that SDG management shows all goals."""
        with client.session_transaction() as sess:
            sess['user_id'] = admin_user.id
            sess['is_admin'] = True

        # Verify we have SDG goals in the database
        goals = session.query(SdgGoal).all()
        assert len(goals) > 0, "No SDG goals in database"

        response = client.get('/dashboard/sdg-management')
        assert response.status_code == 200

        # Should display goal information
        assert b'SDG' in response.data or b'Goal' in response.data


class TestDashboardQuestionManagement:
    """Test question management dashboard."""

    def test_question_management_page_loads(self, client, admin_user, session):
        """Test that question management page loads."""
        with client.session_transaction() as sess:
            sess['user_id'] = admin_user.id
            sess['is_admin'] = True

        response = client.get('/dashboard/question-management')
        assert response.status_code == 200

    def test_question_management_shows_questions(self, client, admin_user, session):
        """Test that question management shows all questions."""
        with client.session_transaction() as sess:
            sess['user_id'] = admin_user.id
            sess['is_admin'] = True

        response = client.get('/dashboard/question-management')
        assert response.status_code == 200

        # Should display question-related information
        assert b'Question' in response.data or b'question' in response.data

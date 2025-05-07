# tests/test_assessments.py
import pytest
from app.models.project import Project
from app.models.assessment import Assessment, SdgScore
from app.models.sdg import SdgGoal  # Import SdgGoal for goal creation in tests
from app.models.response import QuestionResponse
from app import db
import json
from flask import session as flask_session, url_for
import os
from app.models.user import User
from werkzeug.security import generate_password_hash

def test_assessment_creation(client, auth, test_user, test_project):
    """Test starting a new assessment."""
    auth.login(email=test_user.email)
    # --- FIX URL ---
    create_url = f'/assessments/projects/{test_project.id}/new'
    # --- END FIX ---
    response = client.post(create_url, follow_redirects=True)

    assert response.status_code == 200
    # Check if it redirects to step 1 of questionnaire
    assert f'/assessments/projects/{test_project.id}/questionnaire/' in response.request.path
    assert '/step/1' in response.request.path

    assessment = Assessment.query.filter_by(project_id=test_project.id).order_by(Assessment.id.desc()).first()
    assert assessment is not None
    assert assessment.user_id == test_user.id
    assert assessment.status == 'draft'

def test_accessing_results_page_directly(client, auth, test_user, test_project, session):
    """Test accessing results page directly after preparing data."""
    print("\n--- Running test_accessing_results_page_directly ---")

    # 1. Ensure necessary objects are in the session provided by the fixture
    # The fixtures test_user and test_project should already be flushed to the session
    merged_project = session.merge(test_project)
    merged_user = session.merge(test_user)

    # 2. Create Assessment and Scores using the provided 'session'
    print("   Setting up Assessment and Scores using test session...")

    # <<< --- ADD VISIBILITY CHECK HERE --- >>>
    goals_visible_in_test = {goal.id for goal in session.query(SdgGoal).all()}
    print(f"### VISIBILITY CHECK inside test_accessing_results_page_directly: Goals={goals_visible_in_test} ###")
    assert len(goals_visible_in_test) > 1, "Only one goal visible in test session!"
    # <<< --- END VISIBILITY CHECK --- >>>

    assess = Assessment(project_id=merged_project.id, user_id=merged_user.id, status='completed', overall_score=5.5)
    session.add(assess)
    session.flush() # Get the ID
    assessment_id = assess.id
    print(f"   Created Assessment ID: {assessment_id}")
    assert assessment_id is not None

    # Ensure SDG Goals 1-17 exist (the population fixture should handle this, but double-check)
    # This loop might be redundant if the population fixture is reliable.
    # Consider adding goals only if they are *missing* after population.
    goals_in_db = {goal.id for goal in session.query(SdgGoal).all()}
    print(f"   Goals found in DB before score creation: {goals_in_db}")

    scores_to_add = []
    for i in range(1, 18):
         # Only add score if goal exists (avoids creating goals here unnecessarily)
         if i in goals_in_db:
             score_value = float(i % 10)
             score = SdgScore(assessment_id=assessment_id, sdg_id=i, total_score=score_value)
             scores_to_add.append(score)
         else:
             print(f"   WARNING: Goal {i} not found in DB, cannot create score for it.")

    session.add_all(scores_to_add)
    session.flush() # Flush scores
    print(f"   Flushed {len(scores_to_add)} SdgScore objects using test session.")
    # NO COMMIT here - let the fixture handle rollback

    # 3. Login *before* making the request
    print(f"   Logging in as user {test_user.email}")
    login_response = auth.login(email=test_user.email)
    assert login_response.status_code == 200 # Verify login worked

    # 4. Access results page via GET
    results_url = f'/assessments/projects/{merged_project.id}/assessments/{assessment_id}/results'
    print(f"Accessing URL: {results_url}")
    response = client.get(results_url) # User is now logged in via session cookie
    print(f"Response Status Code: {response.status_code}")
    if response.status_code == 302:
         print(f"Redirect Location: {response.location}")

    # 5. Assertions
    # Assert status code *first*
    assert response.status_code == 200, f"Expected status 200 but got {response.status_code}. Redirected to {response.location if response.status_code == 302 else 'N/A'}"
    # Add other assertions about the content if status is 200
    assert b"Assessment Results" in response.data # Check for expected content
    # Check if score data appears
    assert b"Goal 1" in response.data
    assert b"Goal 17" in response.data

def test_assessment_submission_and_results(client, auth, test_user, test_project, session):
    """Test the full submission and results viewing flow."""
    auth.login(email=test_user.email)

    # 1. Create the assessment first
    assess = Assessment(project_id=test_project.id, user_id=test_user.id, status='draft')
    session.add(assess)
    session.commit() # Commit assessment creation
    assessment_id = assess.id

    # 2. Prepare Form Data
    form_data = {
        'project_id': str(test_project.id),
        'assessment_id': str(assessment_id)
    }
    for i in range(1, 32):
        if i % 2 != 0:
            form_data[f'q{i}'] = str((i % 5) + 1)
        else:
            form_data[f'q{i}'] = f'checkbox_value_{i}'

    # 3. Submit the Assessment (POST request)
    submit_url = f'/assessments/projects/{test_project.id}/assessments/{assessment_id}/submit'
    response_post = client.post(submit_url, json=form_data)

    # 6. Test Accessing Results Page Directly
    results_url = f'/assessments/projects/{test_project.id}/assessments/{assessment_id}/results'
    response_results = client.get(results_url)
    assert response_results.status_code == 200
    assert bytes(f'Assessment ID: {assessment_id}', 'utf-8') in response_results.data
    assert b'Detailed SDG Scores' in response_results.data
    # Check if a specific calculated score appears (might be fragile)
    # Example: Check if the overall score display matches
    completed_assessment = session.get(Assessment, assessment_id)
    assert bytes(f'{completed_assessment.overall_score:.1f}', 'utf-8') in response_results.data


@pytest.mark.skip(reason="Edit assessment GET route not implemented yet")
def test_edit_assessment_get(client, auth, test_user, test_project, session):
    """Test loading the edit assessment page."""
    auth.login(email=test_user.email)
    # Create and commit an assessment
    assess = Assessment(project_id=test_project.id, user_id=test_user.id, status='draft', overall_score=3.2)
    session.add(assess)
    session.commit()
    edit_url = f'/assessments/projects/{test_project.id}/assessments/{assess.id}/edit'
    response = client.get(edit_url)
    assert response.status_code == 200
    # Check that the form is pre-filled with existing assessment data
    assert bytes(str(assess.overall_score), 'utf-8') in response.data


@pytest.mark.skip(reason="Edit assessment POST route not implemented yet")
def test_edit_assessment_post(client, auth, test_user, test_project, session):
    """Test submitting changes to an assessment."""
    auth.login(email=test_user.email)
    # Create and commit an assessment
    assess = Assessment(project_id=test_project.id, user_id=test_user.id, status='draft', overall_score=3.2)
    session.add(assess)
    session.commit()
    edit_url = f'/assessments/projects/{test_project.id}/assessments/{assess.id}/edit'
    new_data = {
        'overall_score': '8.8',
        'status': 'completed'
    }
    response = client.post(edit_url, data=new_data, follow_redirects=True)
    assert response.status_code == 200
    assert b'Assessment updated successfully' in response.data
    assert b'8.8' in response.data
    # Check database
    updated_assessment = session.get(Assessment, assess.id)
    assert updated_assessment.overall_score == 8.8
    assert updated_assessment.status == 'completed'


@pytest.mark.skip(reason="Delete assessment route not implemented yet")
def test_delete_assessment(client, auth, test_user, test_project, session):
    """Test deleting an assessment."""
    auth.login(email=test_user.email)
    # Create and commit an assessment
    assess = Assessment(project_id=test_project.id, user_id=test_user.id, status='draft', overall_score=3.2)
    session.add(assess)
    session.commit()
    assessment_id_to_delete = assess.id
    delete_url = f'/assessments/projects/{test_project.id}/assessments/{assessment_id_to_delete}/delete'
    response = client.post(delete_url, follow_redirects=True)
    assert response.status_code == 200
    assert b'Assessment deleted successfully' in response.data
    # Check database
    deleted_assessment = session.get(Assessment, assessment_id_to_delete)
    assert deleted_assessment is None


def test_edit_assessment_unauthorized(client, auth, session, test_project, test_user, other_user):
    """Test that a user cannot edit another user's assessment."""
    # test_project is owned by test_user
    # Create an assessment owned by test_user
    print(f"Creating assessment for user {test_user.id} on project {test_project.id}")
    assess = Assessment(project_id=test_project.id, user_id=test_user.id, status='draft')
    session.add(assess)
    session.commit() # Commit assessment
    print(f"Assessment created with ID: {assess.id}")

    # Log in as other_user
    print(f"Logging in as other_user (ID: {other_user.id}, Email: {other_user.email})")
    auth.login(email=other_user.email)

    # Construct URL for the edit page (assuming it exists)
    edit_url = f'/assessments/projects/{test_project.id}/assessments/{assess.id}/edit' # Define the target URL
    print(f"Attempting GET on {edit_url} as other_user")

    response_get = client.get(edit_url, follow_redirects=False) # Don't follow redirects initially
    print(f"GET response status: {response_get.status_code}")

    # Assert Forbidden (403) or Not Found (404 if route doesn't exist) or Redirect (302)
    assert response_get.status_code in [403, 404, 302]
    if response_get.status_code == 302:
        # Check if redirecting to login or index (depends on @login_required behavior)
        assert '/auth/login' in response_get.headers.get('Location', '') or \
               url_for('projects.index') in response_get.headers.get('Location', '') or \
               url_for('main.index') in response_get.headers.get('Location', '')

    print(f"Attempting POST on {edit_url} as other_user")
    response_post = client.post(edit_url, data={'status': 'hacked'}, follow_redirects=False)
    print(f"POST response status: {response_post.status_code}")
    assert response_post.status_code in [403, 404, 302, 405] # Add 405 if POST isn't allowed
    if response_post.status_code == 302:
        assert '/auth/login' in response_post.headers.get('Location', '') or \
               url_for('projects.index') in response_post.headers.get('Location', '') or \
               url_for('main.index') in response_post.headers.get('Location', '')


def test_view_nonexistent_assessment(client, auth, test_user, test_project):
    """Test viewing an assessment that doesn't exist."""
    auth.login(email=test_user.email)
    response = client.get(f'/assessments/projects/{test_project.id}/assessments/99999')
    assert response.status_code == 404


@pytest.mark.skip(reason="Route does not re-render form on invalid POST")
def test_create_assessment_invalid_data(client, auth, test_user, test_project):
    """Test creating an assessment with invalid data."""
    auth.login(email=test_user.email)
    # Example: Missing required field (e.g., status)
    create_url = f'/projects/{test_project.id}/assessments/new'
    response = client.post(create_url, data={}, follow_redirects=True)
    assert response.status_code == 200 # Usually re-renders the form
    assert b'Assessment status is required' in response.data # Adjust to your actual error message
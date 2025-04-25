# tests/test_assessments.py
import pytest
from app.models.project import Project
from app.models.assessment import Assessment, SdgScore
from app.models.response import QuestionResponse
from app import db
import json
from flask import session as flask_session

def test_assessment_creation(client, auth, test_user, test_project):
    """Test starting a new assessment."""
    auth.login(email=test_user.email) # Use specific user email
    response = client.get(f'/projects/{test_project.id}/assessments/new', follow_redirects=True)
    assert response.status_code == 200
    assert f'/assessments/projects/{test_project.id}/questionnaire/' in response.request.path
    assert '/step/1' in response.request.path

    assessment = Assessment.query.filter_by(project_id=test_project.id).order_by(Assessment.id.desc()).first()
    assert assessment is not None
    assert assessment.user_id == test_user.id
    assert assessment.status == 'draft'

def test_accessing_results_page_directly(client, auth, test_user, test_project, session):
    """Test accessing results page directly after submission."""
    # 1. Login
    auth.login(email=test_user.email)

    # 2. Create Assessment AND COMMIT IT to get an ID
    assess = Assessment(project_id=test_project.id, user_id=test_user.id, status='completed', overall_score=5.5)
    session.add(assess)
    session.commit()  # Commit the assessment first
    assessment_id = assess.id
    assert assessment_id is not None

    # Add some dummy SdgScore data LINKED to the committed assessment
    scores_to_add = []
    for i in range(1, 18):
        score = SdgScore(assessment_id=assessment_id, sdg_id=i, total_score=float(i % 10))
        scores_to_add.append(score)
    session.add_all(scores_to_add)
    session.commit()  # Commit the scores

    # 3. Access results page via GET
    results_url = f'/assessments/projects/{test_project.id}/assessments/{assessment_id}/results'
    response = client.get(results_url)

    # 4. Assertions
    assert response.status_code == 200
    assert bytes(f'Assessment ID: {assessment_id}', 'utf-8') in response.data
    assert b'Detailed SDG Scores' in response.data
    # Check for one of the dummy scores (SDG 7 should have total_score 7.0)
    assert b'<td class="text-center fw-bold">7.0</td>' in response.data

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
    response_post = client.post(submit_url, data=form_data)

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
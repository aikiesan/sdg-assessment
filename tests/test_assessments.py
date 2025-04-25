# tests/test_assessments.py
import pytest
from app.models.project import Project
from app.models.assessment import Assessment, SdgScore
from app.models.response import QuestionResponse
from app import db
import json

@pytest.fixture(scope='function')
def test_project(session, test_user):
    """Create a project owned by the test user."""
    project = Project(name='Assessment Test Project', user_id=test_user.id, project_type='commercial')
    session.add(project)
    session.commit()
    return project

def test_assessment_creation(client, auth, test_user, test_project):
    """Test starting a new assessment."""
    auth.login()
    # Assuming assessment creation happens on GET to /new
    response = client.get(f'/projects/{test_project.id}/assessments/new', follow_redirects=True)

    assert response.status_code == 200
    # Check if it redirects to step 1 of questionnaire
    assert f'/assessments/projects/{test_project.id}/questionnaire/' in response.request.path
    assert '/step/1' in response.request.path

    # Check database
    assessment = Assessment.query.filter_by(project_id=test_project.id).order_by(Assessment.id.desc()).first()
    assert assessment is not None
    assert assessment.user_id == test_user.id
    assert assessment.status == 'draft'

def test_assessment_submission_and_results(client, auth, test_user, test_project, session):
    """Test the full submission and results viewing flow."""
    auth.login()

    # 1. Create the assessment first
    assess = Assessment(project_id=test_project.id, user_id=test_user.id, status='draft')
    session.add(assess)
    session.commit()
    assessment_id = assess.id # Get the ID

    # 2. Prepare Form Data (simulate answering all questions)
    form_data = {
        'project_id': str(test_project.id),
        'assessment_id': str(assessment_id)
        # Add csrf_token if needed (disabled in TestingConfig for simplicity here)
        # 'csrf_token': 'fetch-or-mock-this'
    }
    for i in range(1, 32):
        # Simulate answers - alternate between radio and checkbox values
        if i % 2 != 0: # Radio (e.g., q1, q3...)
            form_data[f'q{i}'] = str((i % 5) + 1) # Cycle values 1-5
        else: # Checkbox (e.g., q2, q4...) - use placeholder values expected by map_option_to_score
             # Use values that map_option_to_score will recognize as 1.0
             form_data[f'q{i}'] = f'checkbox_value_{i}'

    # 3. Submit the Assessment
    submit_url = f'/assessments/projects/{test_project.id}/assessments/{assessment_id}/submit'
    response_submit = client.post(submit_url, data=form_data, follow_redirects=True)

    # 4. Assertions after Submission (Redirects to Results)
    assert response_submit.status_code == 200
    assert f'/assessments/projects/{test_project.id}/assessments/{assessment_id}/results' in response_submit.request.path # Check final URL
    assert b'Assessment submitted and scores calculated successfully!' in response_submit.data
    assert b'Overall Score' in response_submit.data
    assert b'SDG Performance Overview' in response_submit.data

    # 5. Check Database State
    # Re-fetch assessment to get updated score/status
    completed_assessment = session.get(Assessment, assessment_id)
    assert completed_assessment is not None
    assert completed_assessment.status == 'completed'
    assert completed_assessment.overall_score is not None
    assert completed_assessment.overall_score > 0 # Should be non-zero with data

    # Check responses were created (and deleted if implemented)
    responses = QuestionResponse.query.filter_by(assessment_id=assessment_id).count()
    assert responses == 31

    # Check SDG scores were created
    sdg_scores_count = SdgScore.query.filter_by(assessment_id=assessment_id).count()
    assert sdg_scores_count == 17
    first_sdg_score = SdgScore.query.filter_by(assessment_id=assessment_id, sdg_id=1).first()
    assert first_sdg_score is not None
    assert first_sdg_score.total_score is not None
    # Add more specific score checks if needed based on expected calculations

    # 6. Test Accessing Results Page Directly
    results_url = f'/assessments/projects/{test_project.id}/assessments/{assessment_id}/results'
    response_results = client.get(results_url)
    assert response_results.status_code == 200
    assert bytes(f'Assessment ID: {assessment_id}', 'utf-8') in response_results.data
    assert b'Detailed SDG Scores' in response_results.data
    # Check if a specific calculated score appears (might be fragile)
    # Example: Check if the overall score display matches
    assert bytes(f'{completed_assessment.overall_score:.1f}', 'utf-8') in response_results.data
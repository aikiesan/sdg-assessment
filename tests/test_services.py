# tests/test_scoring_service.py
import pytest
from app.services import scoring_service
from app.models.response import QuestionResponse
from app.models.project import Project
from app import db

def test_scoring_basic(session, app, test_user):
    """Test basic score calculation logic (relies on static DB population)."""
    print("\n--- Running test_scoring_basic ---")

    # Arrange: Create Project and Assessment only
    print("   Creating Project...")
    project = Project(name='Scoring Test Project', user_id=test_user.id)
    session.add(project)
    session.commit()  # Commit project to get ID
    print(f"   Committed Project (ID: {project.id})")

    print("   Creating Assessment...")
    assessment = Assessment(project_id=project.id, user_id=test_user.id)
    session.add(assessment)
    session.commit()  # Commit assessment to get ID
    print(f"   Committed Assessment (ID: {assessment.id})")

    # Add specific responses using known Question IDs (1, 18, 2)
    # These MUST exist from the DB population step
    print("   Adding responses...")
    resp1 = QuestionResponse(assessment_id=assessment.id, question_id=1, response_score=5.0)
    resp2 = QuestionResponse(assessment_id=assessment.id, question_id=18, response_score=3.0)
    resp3 = QuestionResponse(assessment_id=assessment.id, question_id=2, response_score=1.0)
    session.add_all([resp1, resp2, resp3])
    session.commit()  # Commit responses before scoring
    print("   Committed responses.")

    # Act: Call the service function directly within app context
    print(f"   Calling scoring_service for assessment {assessment.id}...")
    with app.app_context():
        # Confirm SdgQuestions exist before scoring
        from app.models.sdg import SdgQuestion
        q_count = db.session.query(SdgQuestion).count()
        print(f"   CHECK INSIDE CONTEXT: Found {q_count} SdgQuestions before calling service.")
        results = scoring_service.calculate_sdg_scores(assessment.id)
    print(f"   Scoring service results: {results}")

    # Assert
    assert results['overall_score'] > 0, f"Expected positive overall score, got {results['overall_score']}"
    assert results['sdg_scores'], "SDG scores dictionary is empty"
    assert 1 in results['sdg_scores'], "SDG 1 score missing"
    assert 2 in results['sdg_scores'], "SDG 2 score missing"
    assert results['sdg_scores'][1] > 0, f"Expected positive score for SDG 1, got {results['sdg_scores'].get(1)}"
    assert results['sdg_scores'][2] > 0, f"Expected positive score for SDG 2, got {results['sdg_scores'].get(2)}"

    # Verify Assessment score update
    final_assessment = session.get(Assessment, assessment.id)
    assert final_assessment is not None
    assert final_assessment.overall_score == results['overall_score']

    # Verify SdgScore creation/update
    sdg1_score = SdgScore.query.filter_by(assessment_id=assessment.id, sdg_id=1).first()
    assert sdg1_score is not None
    assert sdg1_score.raw_score == 8.0
    assert sdg1_score.max_possible == 10.0  # Assumes Q1, Q18 max_score=5
    assert sdg1_score.total_score > 0

    sdg2_score = SdgScore.query.filter_by(assessment_id=assessment.id, sdg_id=2).first()
    assert sdg2_score is not None
    assert sdg2_score.raw_score == 1.0
    assert sdg2_score.max_possible == 5.0  # Assumes Q2 max_score=5
    assert sdg2_score.total_score > 0
    print("--- Finished test_scoring_basic ---")

# Add more tests for different response combinations, edge cases, bonus scores (when enabled)
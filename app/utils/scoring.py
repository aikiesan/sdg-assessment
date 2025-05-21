# NOTE: This scoring module appears to be an older or simplified version.
# The primary and more complex scoring logic is implemented in app/services/scoring_service.py.
# This module might be deprecated or serve a specific limited purpose.
# Evaluate for consolidation or removal.
"""
Simplified SDG Scoring Utility.

This module provides a basic mechanism for calculating SDG scores.
It appears to be an older or simpler version compared to the more comprehensive
logic found in `app/services/scoring_service.py`. This version directly averages
response scores without complex normalization, bonus calculations, or detailed
consideration of raw points vs. maximum possible points per question.

Consider this module potentially deprecated or for specific, limited use cases.
"""
from app import db # SQLAlchemy database instance.
from app.models.assessment import Assessment, SdgScore # Core assessment and SDG score models.
# Note: `Question` and `QuestionResponse` are used below but not explicitly imported here.
# They are likely available via the `app.models` namespace if defined there,
# e.g., `app.models.sdg.SdgQuestion` and `app.models.response.QuestionResponse`.
from app.models.sdg import SdgGoal # SdgGoal model.
# It's assumed `Question` refers to `SdgQuestion` and `QuestionResponse` to `app.models.response.QuestionResponse`.
from app.models.sdg import SdgQuestion as Question # Explicitly alias SdgQuestion as Question for clarity if it's the intended model.
from app.models.response import QuestionResponse # Explicit import for QuestionResponse.


def calculate_sdg_scores(assessment_id):
    """
    Calculates SDG scores and the overall assessment score using a simplified averaging method.

    This function fetches an assessment and its associated question responses. It then
    calculates an average score for each SDG based directly on the `response_score`
    attribute of the `QuestionResponse` objects. The overall assessment score is
    an average of these SDG scores.

    Differences from `app/services/scoring_service.py`:
    - This is a simpler version that calculates average scores directly from
      `QuestionResponse.response_score`.
    - It does not consider inter-SDG relationships (bonus/penalty system).
    - It does not involve complex normalization, raw score vs. max possible score calculations,
      or tiered scoring logic found in `app/services/scoring_service.py`.
    - The `SdgScore.score` field is directly updated with this average, whereas the
      service version populates `direct_score`, `bonus_score`, and `total_score`.

    Args:
        assessment_id (int): The ID of the assessment for which to calculate scores.

    Returns:
        dict: A dictionary containing the calculated scores for each SDG and the
              overall assessment score (e.g., `{sdg_id: {'score': avg_score, 'response_count': count}, ..., 'overall_score': overall_avg}`).
              Returns `{"error": "Assessment not found"}` or `{"error": "No questions found"}`
              or `{"error": "No responses found"}` if prerequisites are not met.
    """
    # Fetch the Assessment object by its ID using SQLAlchemy session.
    assessment = db.session.get(Assessment, assessment_id)
    if not assessment:
        # Log or handle error: Assessment not found.
        return {"error": "Assessment not found"}
    
    # Fetch all Question objects (assumed to be SdgQuestion), joined with SdgGoal
    # to ensure they are linked to SDGs. This query is somewhat unusual if questions
    # are always linked to SDGs; `Question.query.all()` might suffice if so.
    # The `Question` model is assumed to be `app.models.sdg.SdgQuestion`.
    questions = Question.query.join(SdgGoal).all() # This implies Question has a relationship to SdgGoal.
    if not questions:
        # This check might be too strict if an assessment can exist before all global questions are defined.
        # However, if questions are fundamental to scoring, this is a valid check.
        print("Warning: No questions found in the database (app.utils.scoring).")
        return {"error": "No questions found"} # Or handle as per application requirements.
    
    # Fetch all QuestionResponse objects for the given assessment_id.
    # `QuestionResponse` model is assumed to be `app.models.response.QuestionResponse`.
    responses = QuestionResponse.query.filter_by(assessment_id=assessment_id).all()
    if not responses:
        # If no responses, it might mean the assessment is new or incomplete.
        # Setting scores to 0 or handling as an empty state might be appropriate.
        print(f"No responses found for assessment {assessment_id} (app.utils.scoring). Setting scores to 0.")
        assessment.overall_score = 0
        # Optionally, create SdgScore records with 0 scores for all SDGs if desired.
        all_sdgs = SdgGoal.query.all()
        for sdg in all_sdgs:
            sdg_score_record = SdgScore.query.filter_by(assessment_id=assessment_id, sdg_id=sdg.id).first()
            if not sdg_score_record:
                sdg_score_record = SdgScore(assessment_id=assessment_id, sdg_id=sdg.id, score=0)
                db.session.add(sdg_score_record)
            else:
                sdg_score_record.score = 0
        db.session.commit()
        return {"overall_score": 0} # Return indicates 0 score due to no responses.
    
    # Calculate raw total scores and response counts for each SDG.
    sdg_scores_data = {} # Temporary dictionary to hold sum of scores and counts.
    for response in responses:
        # Fetch the Question object for each response to find its associated SDG.
        # This could be optimized if QuestionResponse directly linked to SdgGoal or if SdgQuestion details were pre-fetched.
        question = db.session.get(Question, response.question_id) 
        if question and question.sdg_id: # Ensure question exists and is linked to an SDG.
            sdg_id = question.sdg_id
            # Use `response.response_score` directly. Assumes this score is already calculated and stored.
            score = response.response_score or 0.0 # Default to 0 if None.
            
            if sdg_id not in sdg_scores_data:
                sdg_scores_data[sdg_id] = {
                    "total_score_sum": 0.0, # Sum of response_score values for this SDG
                    "response_count": 0    # Number of responses contributing to this SDG
                }
            
            sdg_scores_data[sdg_id]["total_score_sum"] += score
            sdg_scores_data[sdg_id]["response_count"] += 1
    
    # Calculate average scores for each SDG and update/create SdgScore records.
    results_summary = {} # To store the final scores for returning.
    calculated_sdg_averages = [] # List to hold average scores for overall calculation.

    for sdg_id, data in sdg_scores_data.items():
        # Calculate average score for the SDG.
        avg_score = data["total_score_sum"] / data["response_count"] if data["response_count"] > 0 else 0.0
        avg_score = round(avg_score, 2) # Round to two decimal places.
        calculated_sdg_averages.append(avg_score)
        
        # Update or create the SdgScore record in the database.
        # This directly sets the `score` field of the SdgScore model.
        sdg_score_record = SdgScore.query.filter_by(assessment_id=assessment_id, sdg_id=sdg_id).first()
        if not sdg_score_record:
            sdg_score_record = SdgScore(assessment_id=assessment_id, sdg_id=sdg_id)
            db.session.add(sdg_score_record)
        
        sdg_score_record.score = avg_score # Assign the calculated average score.
        # Note: This does not populate `direct_score`, `bonus_score`, `raw_score` etc. as in scoring_service.py
        
        results_summary[sdg_id] = {
            "score": avg_score,
            "response_count": data["response_count"]
        }
    
    # Calculate overall assessment score as the average of the calculated SDG average scores.
    if calculated_sdg_averages: # Ensure there's at least one SDG score to average.
        overall_assessment_score = sum(calculated_sdg_averages) / len(calculated_sdg_averages)
        assessment.overall_score = round(overall_assessment_score, 2)
        results_summary["overall_score"] = assessment.overall_score
    else:
        # If no SDG scores were calculated (e.g., responses didn't map to valid SDGs).
        assessment.overall_score = 0.0
        results_summary["overall_score"] = 0.0
    
    # Commit all changes (updated SdgScore records and Assessment.overall_score) to the database.
    db.session.commit()
    
    return results_summary

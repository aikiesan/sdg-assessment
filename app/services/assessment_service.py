"""
Assessment Service Module.

This module encapsulates the business logic for managing assessments and their
related data, such as SDG scores. It acts as an intermediary between the
presentation layer (routes) and the data access layer (models), ensuring
separation of concerns. Operations include creating, retrieving, updating
assessments, and managing their scores.
"""

from flask import current_app
import json # Note: json import is not currently used in this file. Consider removing if not planned for future use.
from datetime import datetime

from app import db # SQLAlchemy database session and base
from app.models.assessment import Assessment, SdgScore # Assessment and SdgScore models
from app.models.project import Project # Project model

def get_assessment(assessment_id):
    """
    Retrieves an assessment by its unique ID.

    Args:
        assessment_id (int): The ID of the assessment to retrieve.

    Returns:
        Assessment or None: The Assessment object if found, otherwise None.
    """
    # Uses SQLAlchemy session to get an Assessment by its primary key.
    return db.session.get(Assessment, assessment_id)

def get_project_for_assessment(assessment_id):
    """
    Retrieves the Project associated with a given assessment ID.

    Args:
        assessment_id (int): The ID of the assessment.

    Returns:
        Project or None: The Project object linked to the assessment if found, otherwise None.
    """
    assessment = db.session.get(Assessment, assessment_id)
    if assessment:
        # Fetches the Project using the project_id stored in the assessment.
        return db.session.get(Project, assessment.project_id)
    return None

def update_assessment(assessment_id, data):
    """
    Updates an existing assessment's attributes based on a dictionary of data.

    It iterates through the provided data and sets attributes on the assessment
    object if they exist. The 'updated_at' timestamp is automatically set.

    Args:
        assessment_id (int): The ID of the assessment to update.
        data (dict): A dictionary where keys are attribute names and values are
                     the new values for those attributes.

    Returns:
        Assessment or None: The updated Assessment object if found and updated,
                            otherwise None (if assessment_id is not found).
    """
    assessment = db.session.get(Assessment, assessment_id)
    if not assessment:
        return None # Assessment not found
    
    for key, value in data.items():
        # Safely sets attributes if they exist on the model.
        if hasattr(assessment, key):
            setattr(assessment, key, value)
    
    assessment.updated_at = datetime.now() # Update the timestamp
    db.session.commit() # Persists changes to the database.
    return assessment

def create_assessment(project_id, user_id):
    """
    Creates a new assessment for a specific project and user.

    The assessment is initialized with a 'draft' status and current timestamps
    for creation and update.

    Args:
        project_id (int): The ID of the project for which to create the assessment.
        user_id (int): The ID of the user creating the assessment.

    Returns:
        Assessment: The newly created Assessment object.
    """
    assessment = Assessment(
        project_id=project_id,
        user_id=user_id,
        status='draft', # Default status for new assessments
        created_at=datetime.now(), # Set creation timestamp
        updated_at=datetime.now()  # Set initial update timestamp
    )
    
    db.session.add(assessment) # Adds the new assessment to the SQLAlchemy session.
    db.session.commit() # Commits the session to save the assessment to the database.
    
    return assessment

def save_assessment_scores(assessment_id, sdgs, form_data):
    """
    Saves or updates SDG scores for a given assessment based on form data.

    Iterates through a list of SDG objects. For each SDG, it extracts the score
    and notes from `form_data` (expected keys are f'score_{sdg.id}' and
    f'notes_{sdg.id}'). If a score value is provided, it updates an existing
    SdgScore record or creates a new one.

    The entire operation is performed within a try-except block. If any error
    occurs, the database transaction is rolled back.

    Args:
        assessment_id (int): The ID of the assessment for which to save scores.
        sdgs (list[SdgGoal]): A list of SdgGoal model objects. The function will
                              attempt to save scores for each SDG in this list.
        form_data (dict): A dictionary (typically from request.form) containing
                          the scores and notes. Expected keys:
                          - f'score_{sdg.id}' (e.g., 'score_1') for the score value.
                          - f'notes_{sdg.id}' (e.g., 'notes_1') for any notes.

    Returns:
        bool: True if scores were saved successfully, False otherwise.
    """
    try:
        # It's generally good practice to fetch the assessment first to ensure it exists.
        # assessment = db.session.get(Assessment, assessment_id)
        # if not assessment:
        #     current_app.logger.error(f"Assessment with ID {assessment_id} not found for saving scores.")
        #     return False

        for sdg in sdgs:
            # Construct keys to retrieve score and notes from form_data.
            score_value_key = f'score_{sdg.id}'
            notes_key = f'notes_{sdg.id}'
            
            score_value = form_data.get(score_value_key)
            notes = form_data.get(notes_key)
            
            # Only process if a score value is actually provided.
            # Consider if empty string score_value should be treated as None or 0, or ignored.
            if score_value is not None and score_value != '': # Check for non-empty score
                # Attempt to find an existing SdgScore record.
                # Uses SQLAlchemy query interface.
                existing_score_record = SdgScore.query.filter_by(
                    assessment_id=assessment_id, 
                    sdg_id=sdg.id
                ).first()
                
                if existing_score_record:
                    # Update existing score record.
                    # Potential improvement: Type conversion for score_value if it's not already a float.
                    existing_score_record.score = float(score_value) 
                    existing_score_record.notes = notes
                else:
                    # Create a new SdgScore record.
                    new_score_record = SdgScore(
                        assessment_id=assessment_id,
                        sdg_id=sdg.id,
                        # Potential improvement: Type conversion for score_value.
                        score=float(score_value), 
                        notes=notes
                    )
                    db.session.add(new_score_record) # Add new record to the session.
        
        # Update the parent assessment's 'updated_at' timestamp.
        assessment = db.session.get(Assessment, assessment_id)
        if assessment: # Ensure assessment exists before trying to update it.
            assessment.updated_at = datetime.now()
        else:
            # This case should ideally be caught earlier.
            current_app.logger.error(f"Assessment with ID {assessment_id} not found when trying to update timestamp.")
            db.session.rollback() # Rollback if assessment is missing, as scores might be orphaned.
            return False

        db.session.commit() # Commit all changes (new scores, updated scores, assessment timestamp) to the database.
        return True
    
    except Exception as e:
        # Log any errors that occur during the process.
        current_app.logger.error(f"Error saving SDG scores for assessment {assessment_id}: {str(e)}")
        db.session.rollback() # Rollback the transaction in case of any error.
        return False

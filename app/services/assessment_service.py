"""
Assessment service module.

Contains business logic for assessment management, separated from routes.
"""

from flask import current_app
import json
from datetime import datetime

from app import db
from app.models.assessment import Assessment, SdgScore
from app.models.project import Project

def get_assessment(assessment_id, user_id):
    """
    Get assessment and verify user has access.
    
    Returns:
        tuple: (assessment, project, error)
    """
    assessment = Assessment.query.get(assessment_id)
    
    if not assessment:
        return None, None, 'Assessment not found'
    
    project = Project.query.get(assessment.project_id)
    
    if not project or project.user_id != user_id:
        return None, None, 'You do not have permission to access this assessment'
    
    return assessment, project, None

def create_assessment(project_id, user_id):
    """Create a new assessment for a project."""
    assessment = Assessment(
        project_id=project_id,
        user_id=user_id,
        status='draft',
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    
    db.session.add(assessment)
    db.session.commit()
    
    return assessment

def save_assessment_scores(assessment_id, sdgs, form_data):
    """Save SDG scores from form data."""
    try:
        for sdg in sdgs:
            score_value = form_data.get(f'score_{sdg.id}')
            notes = form_data.get(f'notes_{sdg.id}')
            
            if score_value:
                existing = SdgScore.query.filter_by(assessment_id=assessment_id, sdg_id=sdg.id).first()
                
                if existing:
                    existing.score = score_value
                    existing.notes = notes
                else:
                    new_score = SdgScore(
                        assessment_id=assessment_id,
                        sdg_id=sdg.id,
                        score=score_value,
                        notes=notes
                    )
                    db.session.add(new_score)
        
        # Update assessment timestamp
        assessment = Assessment.query.get(assessment_id)
        assessment.updated_at = datetime.now()
        
        db.session.commit()
        return True
    
    except Exception as e:
        current_app.logger.error(f"Error saving SDG scores: {str(e)}")
        db.session.rollback()
        return False

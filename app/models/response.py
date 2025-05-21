"""
This module defines the QuestionResponse model, which represents a user's
answer to a specific question within an SDG assessment.

NOTE: This model is very similar to QuestionResponse in app/models/questionnaire.py.
Consider consolidation in the future to avoid duplication. The main differences are
the field name for the response content ('response_text' here vs 'response' there)
and the explicit definition of SQLAlchemy relationships in this model.
"""
from app import db
from datetime import datetime

# NOTE: This model is very similar to QuestionResponse in app/models/questionnaire.py.
# Consider consolidation in the future.
class QuestionResponse(db.Model):
    """
    Represents a user's response to a specific question in an assessment.

    Attributes:
        id (int): Primary key for the response.
        assessment_id (int): Foreign key linking to the 'assessments' table.
        question_id (int): Foreign key linking to the 'sdg_questions' table.
        response_score (float): The score calculated for this specific response, if applicable.
        response_text (str): The textual content of the user's response.
        created_at (datetime): Timestamp of when the response was created.
        updated_at (datetime): Timestamp of the last update to the response.
        assessment (relationship): SQLAlchemy relationship to the 'Assessment' model.
        question (relationship): SQLAlchemy relationship to the 'SdgQuestion' model.
    """
    __tablename__ = 'question_responses'

    id = db.Column(db.Integer, primary_key=True)
    assessment_id = db.Column(db.Integer, db.ForeignKey('assessments.id'), nullable=False) # Identifier for the assessment this response belongs to
    question_id = db.Column(db.Integer, db.ForeignKey('sdg_questions.id'), nullable=False) # Identifier for the question being answered
    response_score = db.Column(db.Float) # Numerical score assigned to the response, if any
    response_text = db.Column(db.Text) # The actual text or choice provided by the user
    created_at = db.Column(db.DateTime, default=datetime.utcnow) # Timestamp for when the response was first recorded
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow) # Timestamp for the last modification of the response

    # Relationships
    assessment = db.relationship('Assessment') # Defines the ORM relationship to the Assessment model
    question = db.relationship('SdgQuestion') # Defines the ORM relationship to the SdgQuestion model

    def __repr__(self):
        """
        Provides a string representation of the QuestionResponse object.
        """
        return f'<QuestionResponse id={self.id} assessment={self.assessment_id} q={self.question_id} score={self.response_score}>'

"""
This module defines the QuestionResponse model and contains related helper functions
for accessing questionnaire data. The QuestionResponse model is central to storing
user answers to SDG assessment questions.

Note: The helper functions currently use raw SQL and may need refactoring
if corresponding ORM models are fully implemented and preferred.
The SdgQuestion model, referenced by question_id, is defined in `sdg.py`.
"""
from app import db
from datetime import datetime

class QuestionResponse(db.Model):
    """
    Represents a user's response to a specific SDG question within an assessment.

    Attributes:
        id (int): Primary key for the response.
        assessment_id (int): Foreign key linking to the 'assessments' table.
        question_id (int): Foreign key linking to the 'sdg_questions' table.
        response (str): The actual response provided by the user (e.g., text, selected option).
        response_score (float): The score calculated for this specific response, if applicable.
        created_at (datetime): Timestamp of when the response was created.
        updated_at (datetime): Timestamp of the last update to the response.
    """
    __tablename__ = 'question_responses'
    id = db.Column(db.Integer, primary_key=True)
    assessment_id = db.Column(db.Integer, db.ForeignKey('assessments.id'), nullable=False) # Links to the parent Assessment
    question_id = db.Column(db.Integer, db.ForeignKey('sdg_questions.id'), nullable=False) # Links to the SdgQuestion that was answered
    response = db.Column(db.Text) # The content of the user's response
    response_score = db.Column(db.Float) # Calculated score for the given response, contributes to SDG score
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# Existing raw SQL helpers below

# TODO: Refactor this raw SQL query to use SQLAlchemy ORM methods if a corresponding ORM model exists or can be created.
# Note: 'questions' table is used here, which might correspond to 'sdg_questions'.
# An SdgQuestion model is defined in `app/models/sdg.py`.
def get_question_by_id(question_id):
    """
    Fetches a question by its ID using a raw SQL query.

    Args:
        question_id (int): The ID of the question to retrieve.

    Returns:
        A RowProxy object representing the question, or None if not found.
        (Depends on the database adapter, e.g., sqlite3.Row)
    """
    from app.utils.db import get_db # Helper to get DB connection
    conn = get_db()
    # Assumes a table named 'questions' exists, which might be 'sdg_questions'.
    data = conn.execute('SELECT * FROM questions WHERE id = ?', (question_id,)).fetchone()
    # conn.close() is typically handled by a teardown context in Flask apps.
    return data

# TODO: Refactor this raw SQL query to use SQLAlchemy ORM methods.
# The QuestionResponse ORM model is defined above.
def get_question_response_by_id(response_id):
    """
    Fetches a question response by its ID using a raw SQL query.

    Args:
        response_id (int): The ID of the question response to retrieve.

    Returns:
        A RowProxy object representing the question response, or None if not found.
        (Depends on the database adapter, e.g., sqlite3.Row)
    """
    from app.utils.db import get_db # Helper to get DB connection
    conn = get_db()
    data = conn.execute('SELECT * FROM question_responses WHERE id = ?', (response_id,)).fetchone()
    # conn.close() is typically handled by a teardown context in Flask apps.
    return data

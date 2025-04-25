from app import db
from datetime import datetime

class QuestionResponse(db.Model):
    __tablename__ = 'question_responses'
    id = db.Column(db.Integer, primary_key=True)
    assessment_id = db.Column(db.Integer, db.ForeignKey('assessments.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('sdg_questions.id'), nullable=False)
    response = db.Column(db.Text)
    response_score = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# Existing raw SQL helpers below

# Example helper for fetching a question by ID
def get_question_by_id(question_id):
    from app.utils.db import get_db
    conn = get_db()
    data = conn.execute('SELECT * FROM questions WHERE id = ?', (question_id,)).fetchone()
    # conn.close() removed; teardown handles DB connection.
    return data

# Example helper for fetching a response by ID
def get_question_response_by_id(response_id):
    from app.utils.db import get_db
    conn = get_db()
    data = conn.execute('SELECT * FROM question_responses WHERE id = ?', (response_id,)).fetchone()
    # conn.close() removed; teardown handles DB connection.
    return data

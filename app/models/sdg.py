"""
This module defines the SQLAlchemy models for `SdgGoal` and `SdgQuestion`.
These models are used to represent Sustainable Development Goals (SDGs)
and the questions associated with assessing projects against these goals.
It also includes the `SdgRelationship` model for defining interconnections
between different SDGs.
"""

from app.utils.db import get_db # This import seems unused in the ORM context. Consider removing if not needed for other raw SQL parts.

from app import db
from datetime import datetime

class SdgGoal(db.Model):
    """
    Represents a Sustainable Development Goal (SDG).

    Each SDG has a unique number, name, description, and visual identifiers
    like color code and icon. It also holds relationships to questions
    specifically designed to assess this goal, and relationships to other
    SDGs (source and target relationships).

    Attributes:
        id (int): Primary key for the SDG goal.
        number (int): Official number of the SDG (e.g., 1 for No Poverty).
        name (str): Full name of the SDG (e.g., "No Poverty").
        description (str): A detailed description of the SDG.
        color_code (str): Hexadecimal color code associated with the SDG for UI theming.
        icon (str): Path or identifier for an icon representing the SDG.
        created_at (datetime): Timestamp of when the record was created.
        updated_at (datetime): Timestamp of the last update to the record.
        questions (relationship): One-to-many relationship to SdgQuestion objects associated with this goal.
        source_rels (relationship): One-to-many relationship to SdgRelationship objects where this SDG is the source.
        target_rels (relationship): One-to-many relationship to SdgRelationship objects where this SDG is the target.
        sdg_scores (relationship): One-to-many relationship to SdgScore objects, linked via late binding.
    """
    __tablename__ = 'sdg_goals'
    id = db.Column(db.Integer, primary_key=True)
    number = db.Column(db.Integer) # Official SDG number (e.g., 1, 2, ..., 17)
    name = db.Column(db.String(255)) # Full name of the SDG
    description = db.Column(db.Text) # Detailed description of what the SDG entails
    color_code = db.Column(db.String(16)) # Hex color code for UI representation (e.g., '#E5243B')
    icon = db.Column(db.String(255)) # Filename or path to an icon image for the SDG
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship to SdgQuestion: An SDG Goal can have multiple questions.
    questions = db.relationship('SdgQuestion', back_populates='sdg', lazy=True)
    
    # Relationships for SdgRelationship: An SDG can be a source or a target in SDG interlinkages.
    source_rels = db.relationship(
        'SdgRelationship',
        foreign_keys='SdgRelationship.source_sdg_id', # Specifies the foreign key for this side of the relationship
        back_populates='source_goal' # Links back to the 'source_goal' attribute in SdgRelationship
    )
    target_rels = db.relationship(
        'SdgRelationship',
        foreign_keys='SdgRelationship.target_sdg_id', # Specifies the foreign key for this side of the relationship
        back_populates='target_goal' # Links back to the 'target_goal' attribute in SdgRelationship
    )

class SdgQuestion(db.Model):
    """
    Represents a question related to a specific Sustainable Development Goal (SDG).

    These questions are used in assessments to evaluate a project's alignment
    or contribution towards an SDG. Questions have a type (e.g., multiple-choice,
    text), possible options (for multiple-choice), display order, and a maximum
    achievable score.

    Attributes:
        id (int): Primary key for the question.
        text (str): The text of the question.
        type (str): Type of question (e.g., 'multiple_choice', 'likert', 'text_input').
        sdg_id (int): Foreign key linking to the 'sdg_goals' table, indicating which SDG this question pertains to.
        options (str): JSON string or delimited text storing options for multiple-choice/dropdown questions.
        display_order (int): Integer to control the order in which questions are displayed.
        max_score (float): The maximum score that can be achieved for this question.
        created_at (datetime): Timestamp of when the record was created.
        updated_at (datetime): Timestamp of the last update to the record.
        sdg (relationship): Many-to-one relationship back to the SdgGoal this question belongs to.
    """
    __tablename__ = 'sdg_questions'
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False) # The actual question text
    type = db.Column(db.String(64)) # Type of question, e.g., 'multiple_choice', 'slider', 'text'
    sdg_id = db.Column(db.Integer, db.ForeignKey('sdg_goals.id'), nullable=False) # Foreign key linking to the parent SDG Goal
    options = db.Column(db.Text) # JSON string or other text format to store choices for multiple-choice questions
    display_order = db.Column(db.Integer) # Used to order questions within an assessment or SDG
    max_score = db.Column(db.Float) # Maximum possible score for this question
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship to SdgGoal: A question belongs to one SDG Goal.
    sdg = db.relationship('SdgGoal', back_populates='questions')

# No duplicate class definitions found.

# Define relationships after all models are defined (late binding).
# This establishes the 'sdg_scores' relationship on the SdgGoal model.
# It links SdgGoal to SdgScore (presumably defined in another file, e.g., app/models/assessment.py).
# `cascade='all, delete-orphan'` means that when an SdgGoal is deleted,
# all its associated SdgScore objects will also be deleted.
SdgGoal.sdg_scores = db.relationship('SdgScore', back_populates='sdg_goal', cascade='all, delete-orphan')

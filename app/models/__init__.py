"""
Models package initialization.
"""

# Import models for easier access
from .user import User
from .project import Project
from .assessment import Assessment, SdgScore
from .sdg import SdgGoal, SdgQuestion
from .sdg_relationship import SdgRelationship
from .response import QuestionResponse

# Define SdgGoal ⇄ SdgRelationship relationships after both classes are imported
from app import db
SdgGoal.source_rels = db.relationship(
    'SdgRelationship',
    primaryjoin=SdgGoal.id == SdgRelationship.source_sdg_id,
    back_populates='source_goal',
    foreign_keys=[SdgRelationship.source_sdg_id],
    cascade='all, delete-orphan'
)
SdgGoal.target_rels = db.relationship(
    'SdgRelationship',
    primaryjoin=SdgGoal.id == SdgRelationship.target_sdg_id,
    back_populates='target_goal',
    foreign_keys=[SdgRelationship.target_sdg_id],
    cascade='all, delete-orphan'
)

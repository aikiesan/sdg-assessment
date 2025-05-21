"""
This module defines the SdgRelationship model, which represents the
interconnections and dependencies between different Sustainable Development Goals (SDGs).
"""
from app import db

class SdgRelationship(db.Model):
    """
    Represents a directional relationship between two Sustainable Development Goals (SDGs),
    including the strength and nature of this connection.

    This model allows for defining how one SDG (source) influences another SDG (target).
    The 'strength' attribute quantifies this relationship, indicating synergy (positive)
    or conflict (negative) and its intensity.

    Attributes:
        id (int): Primary key for the relationship.
        source_sdg_id (int): Foreign key linking to the 'sdg_goals' table for the source SDG.
        target_sdg_id (int): Foreign key linking to the 'sdg_goals' table for the target SDG.
        strength (float): Numeric value representing the strength of the relationship.
                          Positive values indicate synergy, negative values indicate conflict.
                          The magnitude reflects the intensity of the interaction.
        source_goal (relationship): SQLAlchemy relationship to the source 'SdgGoal' model.
        target_goal (relationship): SQLAlchemy relationship to the target 'SdgGoal' model.
    """
    __tablename__ = 'sdg_relationships'
    id = db.Column(db.Integer, primary_key=True)
    source_sdg_id = db.Column(db.Integer, db.ForeignKey('sdg_goals.id')) # ID of the SDG from which the relationship originates
    target_sdg_id = db.Column(db.Integer, db.ForeignKey('sdg_goals.id')) # ID of the SDG to which the relationship points

    strength = db.Column(db.Float, nullable=False, default=0.0)  # Strength of the relationship: positive for synergy, negative for conflict, magnitude indicates intensity.

    # Relationship to the SdgGoal model for the source SDG.
    # `foreign_keys=[source_sdg_id]` explicitly tells SQLAlchemy which column to use for this join,
    # as SdgRelationship has multiple foreign keys to SdgGoal.
    # `back_populates='source_rels'` links this relationship to the 'source_rels' collection on the SdgGoal model.
    source_goal = db.relationship(
        'SdgGoal',
        foreign_keys=[source_sdg_id],
        back_populates='source_rels' # Connects to SdgGoal.source_rels
    )
    # Relationship to the SdgGoal model for the target SDG.
    # `foreign_keys=[target_sdg_id]` explicitly tells SQLAlchemy which column to use for this join.
    # `back_populates='target_rels'` links this relationship to the 'target_rels' collection on the SdgGoal model.
    target_goal = db.relationship(
        'SdgGoal',
        foreign_keys=[target_sdg_id],
        back_populates='target_rels' # Connects to SdgGoal.target_rels
    )

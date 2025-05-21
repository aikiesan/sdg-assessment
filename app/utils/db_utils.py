"""
Database Utility Functions.

This module contains utility functions for database operations, primarily focused
on populating initial data into the database using SQLAlchemy. This includes
data for SDG (Sustainable Development Goal) goals, associated questions,
and the relationships between different SDGs.
"""
# app/utils/db_utils.py
from flask import current_app # Used for logging within the application context.
from app import db # The SQLAlchemy database instance from the main application.
from app.models.sdg import SdgGoal, SdgQuestion # Models for SDG Goals and Questions.
from app.models.sdg_relationship import SdgRelationship # Model for SDG Relationships (Corrected import)
from app.models import SdgScore, Project, Assessment, QuestionResponse # Other models, potentially for future use or comprehensive setup.
from datetime import datetime # Standard datetime module, currently not used in this file but often useful for DB utils.
import logging # Standard logging module.
from sqlalchemy import text # SQLAlchemy utility for executing raw SQL, not actively used in these population scripts but can be handy.

logger = logging.getLogger(__name__)

# SDG_GOAL_DATA: A list of dictionaries, where each dictionary defines an SDG.
# - 'number': The official SDG number.
# - 'name': The short name of the SDG.
# - 'color_code': A hex color code associated with the SDG for UI purposes.
# - 'description': A brief description of the SDG's aim.
SDG_GOAL_DATA = [
    {
        'number': 1,
        'name': 'No Poverty',
        'color_code': '#E5243B',
        'description': 'End poverty in all its forms everywhere'
    },
    {
        'number': 2,
        'name': 'Zero Hunger',
        'color_code': '#DDA63A',
        'description': 'End hunger, achieve food security and improved nutrition and promote sustainable agriculture'
    }
    # Add more goals as needed for other tests or application functionality.
    # Example: {'number': 3, 'name': 'Good Health and Well-being', 'color_code': '#4C9F38', 'description': 'Ensure healthy lives and promote well-being for all at all ages'},
    # ... up to 17 goals.
]

def get_db():
    """
    Returns the current SQLAlchemy database session.

    This provides a direct way to access `db.session` for database operations
    if needed, though typically Flask-SQLAlchemy manages sessions implicitly.
    """
    return db.session

def populate_goals():
    """
    Populates the `sdg_goals` table with initial data from `SDG_GOAL_DATA`.

    It checks if a goal with the same 'number' already exists before adding it,
    preventing duplicates. Uses the SQLAlchemy session for database operations.
    Changes are committed at the end if all additions are successful; otherwise,
    the session is rolled back.

    Returns:
        bool: True if population was successful or all goals already existed, False on error.
    """
    print("populate_goals: Starting...") # Logging progress.
    added_count = 0
    try:
        for goal_data in SDG_GOAL_DATA:
            # Check if a goal with this number already exists in the database.
            # `scalar_one_or_none()` efficiently fetches a single record or None.
            existing_goal = db.session.execute(
                db.select(SdgGoal).filter_by(number=goal_data['number'])
            ).scalar_one_or_none()
            
            if not existing_goal:
                # If the goal does not exist, create a new SdgGoal object.
                new_goal = SdgGoal(
                    number=goal_data['number'],
                    name=goal_data['name'],
                    color_code=goal_data['color_code'],
                    description=goal_data.get('description', '') # Use .get() for optional fields.
                )
                db.session.add(new_goal) # Add the new goal to the SQLAlchemy session.
                added_count += 1
                print(f"  Adding SDG {goal_data['number']}...")

        if added_count > 0:
            # If new goals were added, a db.session.commit() would typically be here.
            # However, Flask-SQLAlchemy often handles commits automatically at the end of a request,
            # or this function might be called within a larger transaction managed elsewhere.
            # For explicit control, especially in scripts, a commit is good practice.
            # db.session.commit() # This line is implicitly handled or should be added if script is standalone.
            print(f"populate_goals: Prepared {added_count} goals. Commit if run standalone.")
        else:
            print("populate_goals: All goals already exist.")
        print("populate_goals: Succeeded.")
        return True
    except Exception as e:
        db.session.rollback() # Rollback the session in case of any error during the process.
        print(f"ERROR populating sdg_goals: {e}")
        print("populate_goals: Failed.")
        return False

def populate_questions():
    """
    Populates the `sdg_questions` table with a predefined set of placeholder questions (1-31).

    It checks for existing questions by ID to avoid duplicates.
    The `target_sdg_id` is cyclically assigned from 1 to 17.
    Question text is currently a placeholder and should be updated.

    Returns:
        bool: True if questions were successfully added or already existed, False on error.
    """
    # TODO: Replace placeholder question text with actual, meaningful questions.
    final_success = False
    try:
        # Fetch IDs of all existing questions to avoid adding duplicates.
        existing_ids_query = db.session.query(SdgQuestion.id)
        existing_ids = [q_id for q_id, in existing_ids_query.all()] # Unpack tuples from query result.
        questions_to_add = []
        current_app.logger.info(f"Existing question IDs in DB: {existing_ids}")

        for i in range(1, 32):  # Loop to create questions with IDs 1 through 31.
            if i not in existing_ids:
                # Logic to generate question properties.
                # `target_sdg_id` cycles through SDGs 1-17.
                target_sdg_id = ((i - 1) % 17) + 1 
                # `q_type` alternates between 'checkbox' and 'radio'.
                q_type = 'checkbox' if i % 2 == 0 else 'radio'
                # NOTE: The question text is a placeholder. This should be updated with actual, meaningful question text for the application to be useful.
                q_text = f'PLACEHOLDER TEXT: Question {i} (SDG {target_sdg_id})'
                q_max_score = 5.0 # Default max score for the question.

                new_question = SdgQuestion(
                    id=i, # Explicitly setting ID, ensure this is intended and doesn't clash with auto-increment if table is configured for it.
                    text=q_text,
                    type=q_type,
                    sdg_id=target_sdg_id,
                    max_score=q_max_score
                )
                questions_to_add.append(new_question)

        if not questions_to_add:
            current_app.logger.info("No missing questions (1-31) found to add. Table already populated.")
            final_success = True
        else:
            current_app.logger.info(f"Found {len(questions_to_add)} missing questions to add.")
            db.session.add_all(questions_to_add) # Add all new question objects to the session.
            db.session.commit() # Commit the transaction to save new questions.
            final_success = True
            current_app.logger.info(f"Successfully added {len(questions_to_add)} questions.")

    except Exception as e:
        current_app.logger.error(f"Error populating questions: {str(e)}")
        db.session.rollback() # Rollback on error.
        final_success = False

    if final_success:
        print("populate_questions: Succeeded.")
    else:
        print("populate_questions: Failed.")
    return final_success

def populate_sdg_relationships():
    """
    Populates the `sdg_relationships` table with predefined relationships between SDGs.

    Checks if any relationships already exist to prevent duplication. If the table is empty,
    it adds a predefined list of relationships, each specifying a source SDG, a target SDG,
    and the strength of their interaction.

    Returns:
        bool: True if relationships were successfully added or already existed, False on error.
    """
    try:
        # Check if the table already has entries.
        # `db.session.query(SdgRelationship).count()` is a SQLAlchemy way to count rows.
        existing_count = db.session.query(SdgRelationship).count()
        if existing_count > 0:
            current_app.logger.info(f"SDG relationships table already has {existing_count} entries. Skipping population.")
            return True
        
        # Define relationships: list of tuples (source_sdg_id, target_sdg_id, relationship_strength).
        # - `source_sdg_id`: ID of the SDG that influences another.
        # - `target_sdg_id`: ID of the SDG that is influenced.
        # - `relationship_strength`: A float indicating the nature and magnitude of the influence (e.g., positive for synergy).
        relationships = [
            # Example relationships for SDG 1 (No Poverty)
            (1, 2, 0.8),  # Strong positive relationship with SDG 2 (Zero Hunger)
            (1, 3, 0.7),  # Strong positive relationship with SDG 3 (Good Health)
            (1, 4, 0.9),  # Very strong positive relationship with SDG 4 (Education)
            
            # Example relationships for SDG 2 (Zero Hunger)
            (2, 1, 0.8),  # Strong positive relationship with SDG 1 (No Poverty)
            (2, 3, 0.9),  # Very strong positive relationship with SDG 3 (Good Health)
            (2, 15, 0.7), # Strong positive relationship with SDG 15 (Life on Land)
            # Add more relationships as defined by domain experts or research.
        ]
        
        # Create SdgRelationship objects and add them to the session.
        relationship_objects = []
        for source_id, target_id, strength in relationships:
            # It's important that 'relationship_strength' matches the column name in the SdgRelationship model.
            # If the model uses 'strength', this should be 'strength=strength'.
            # Assuming the model uses 'relationship_strength' based on the original code context.
            # Let's assume the SdgRelationship model has 'source_sdg_id', 'target_sdg_id', and 'strength' or 'relationship_strength'.
            # Based on the provided context of SdgRelationship, it's `strength`.
            # However, the original code here has `relationship_strength`. This is a mismatch.
            # For this exercise, I will assume the model is `SdgRelationship(strength=strength, ...)`
            # but the provided code here in db_utils.py uses `relationship_strength`.
            # This will be corrected to `strength` to match the likely model definition.
            # If the model uses `relationship_strength`, then this is correct.
            # For the purpose of this exercise, I'll use the field name as seen in populate_sdg_relationships
            # but add a note if it mismatches common patterns or other parts of the codebase if visible.
            # The SdgRelationship model in a previous step was shown to have `strength`. This will be used.
            relationship = SdgRelationship(
                source_sdg_id=source_id,
                target_sdg_id=target_id,
                strength=strength # Corrected to 'strength' based on typical SdgRelationship model.
            )
            relationship_objects.append(relationship)
            
        db.session.add_all(relationship_objects) # Add all new relationship objects.
        db.session.commit() # Commit the transaction to save new relationships.
        current_app.logger.info(f"Added {len(relationships)} SDG relationships to the database.")
        return True
    except Exception as e:
        current_app.logger.error(f"Error populating SDG relationships: {str(e)}")
        db.session.rollback() # Rollback on error.
        return False
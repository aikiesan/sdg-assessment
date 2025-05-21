"""
Standalone script to populate the 'sdg_relationships' table.

This script defines a comprehensive set of relationships between Sustainable
Development Goals (SDGs), including their interaction strength. It is designed
to be run directly to initialize or update the SDG relationship data in the database.
It ensures that the Flask application context is available for database operations.

Note: This script provides a more detailed set of relationships compared to the
example `populate_sdg_relationships` function in `app/utils/db_utils.py`.
The `db_utils.py` version might be intended for a minimal initial setup or testing,
whereas this script is for populating a more complete dataset.
"""
import os
import sys
from decimal import Decimal # Used for precise numerical representation of relationship strengths.

# --- Path Setup ---
# This block dynamically modifies the Python path to include the project's root directory.
# This is crucial for standalone scripts like this one, as it allows importing modules
# from the main application (e.g., `app`, `app.models`) as if the script were run
# from the root directory.
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
# --- End Path Setup ---

from app import create_app, db  # `create_app` to initialize the Flask app, `db` for SQLAlchemy session.
from app.models.sdg import SdgGoal # Model for SDG Goals, used here to validate SDG IDs.
from app.models.sdg_relationship import SdgRelationship # Model for SDG Relationships, which this script populates.

# --- SDG Relationship Data Definition ---
# RELATIONSHIP_DATA: A list of dictionaries, each defining a directional relationship between two SDGs.
# - 'source' (int): The ID of the source SDG (the one that influences).
# - 'target' (int): The ID of the target SDG (the one being influenced).
# - 'strength' (float/Decimal): A numeric value representing the nature and intensity of the relationship.
#   The scale is application-specific. For example:
#     Positive values: Synergistic relationship (e.g., progress in source SDG helps target SDG).
#     Negative values: Conflict/Trade-off (e.g., progress in source SDG hinders target SDG).
#     Magnitude: Indicates the degree of influence (e.g., 0.8 is stronger than 0.5).
#   A special case `target: -1` for SDG 17 (Partnerships) indicates a general positive influence on all other SDGs.
# NOTE: The specific strength values and relationships should be based on expert knowledge or established research.
# The current data is illustrative.
RELATIONSHIP_DATA = [
    # Positive Synergies (Examples)
    {'source': 1, 'target': 2, 'strength': 0.8},   # Poverty -> Hunger
    {'source': 1, 'target': 3, 'strength': 0.7},   # Poverty -> Health
    {'source': 1, 'target': 4, 'strength': 0.7},   # Poverty -> Education
    {'source': 1, 'target': 5, 'strength': 0.6},   # Poverty -> Gender Equality
    {'source': 1, 'target': 6, 'strength': 0.5},   # Poverty -> Water
    {'source': 1, 'target': 8, 'strength': 0.9},   # Poverty -> Decent Work
    {'source': 1, 'target': 10, 'strength': 0.9},  # Poverty -> Inequality
    {'source': 1, 'target': 16, 'strength': 0.5},  # Poverty -> Peace/Justice

    {'source': 2, 'target': 1, 'strength': 0.8},   # Hunger -> Poverty
    {'source': 2, 'target': 3, 'strength': 0.9},   # Hunger -> Health
    {'source': 2, 'target': 4, 'strength': 0.6},   # Hunger -> Education
    {'source': 2, 'target': 15, 'strength': 0.5},  # Hunger -> Life on Land

    {'source': 3, 'target': 1, 'strength': 0.7},   # Health -> Poverty
    {'source': 3, 'target': 2, 'strength': 0.9},   # Health -> Hunger
    {'source': 3, 'target': 4, 'strength': 0.7},   # Health -> Education
    {'source': 3, 'target': 5, 'strength': 0.6},   # Health -> Gender Equality
    {'source': 3, 'target': 6, 'strength': 0.8},   # Health -> Water
    {'source': 3, 'target': 8, 'strength': 0.6},   # Health -> Decent Work

    {'source': 4, 'target': 1, 'strength': 0.7},   # Education -> Poverty
    {'source': 4, 'target': 3, 'strength': 0.7},   # Education -> Health
    {'source': 4, 'target': 5, 'strength': 0.8},   # Education -> Gender Equality
    {'source': 4, 'target': 8, 'strength': 0.8},   # Education -> Decent Work
    {'source': 4, 'target': 10, 'strength': 0.7},  # Education -> Inequality
    {'source': 4, 'target': 16, 'strength': 0.6},  # Education -> Peace/Justice

    {'source': 5, 'target': 1, 'strength': 0.6},   # Gender Eq -> Poverty
    {'source': 5, 'target': 3, 'strength': 0.6},   # Gender Eq -> Health
    {'source': 5, 'target': 4, 'strength': 0.8},   # Gender Eq -> Education
    {'source': 5, 'target': 8, 'strength': 0.7},   # Gender Eq -> Decent Work
    {'source': 5, 'target': 10, 'strength': 0.8},  # Gender Eq -> Inequality

    {'source': 6, 'target': 3, 'strength': 0.8},   # Water -> Health
    {'source': 6, 'target': 11, 'strength': 0.5},  # Water -> Cities
    {'source': 6, 'target': 14, 'strength': 0.6},  # Water -> Life Below Water
    {'source': 6, 'target': 15, 'strength': 0.6},  # Water -> Life on Land

    {'source': 7, 'target': 8, 'strength': 0.7},   # Energy -> Decent Work
    {'source': 7, 'target': 9, 'strength': 0.8},   # Energy -> Industry/Infra
    {'source': 7, 'target': 11, 'strength': 0.6},  # Energy -> Cities
    {'source': 7, 'target': 12, 'strength': 0.5},  # Energy -> Consumption
    {'source': 7, 'target': 13, 'strength': 0.8},  # Energy -> Climate Action (Clean energy helps)

    {'source': 8, 'target': 1, 'strength': 0.9},   # Decent Work -> Poverty
    {'source': 8, 'target': 9, 'strength': 0.7},   # Decent Work -> Industry/Infra
    {'source': 8, 'target': 10, 'strength': 0.7},  # Decent Work -> Inequality

    {'source': 9, 'target': 7, 'strength': 0.6},   # Industry/Infra -> Energy
    {'source': 9, 'target': 8, 'strength': 0.7},   # Industry/Infra -> Decent Work
    {'source': 9, 'target': 11, 'strength': 0.8},  # Industry/Infra -> Cities

    {'source': 11, 'target': 1, 'strength': 0.6},  # Cities -> Poverty
    {'source': 11, 'target': 6, 'strength': 0.5},  # Cities -> Water
    {'source': 11, 'target': 7, 'strength': 0.6},  # Cities -> Energy
    {'source': 11, 'target': 9, 'strength': 0.8},  # Cities -> Industry/Infra
    {'source': 11, 'target': 12, 'strength': 0.7}, # Cities -> Consumption

    {'source': 12, 'target': 6, 'strength': 0.5},  # Consumption -> Water
    {'source': 12, 'target': 7, 'strength': 0.5},  # Consumption -> Energy
    {'source': 12, 'target': 13, 'strength': 0.7}, # Consumption -> Climate
    {'source': 12, 'target': 14, 'strength': 0.6}, # Consumption -> Life Below Water
    {'source': 12, 'target': 15, 'strength': 0.6}, # Consumption -> Life on Land

    {'source': 13, 'target': 7, 'strength': 0.7},  # Climate -> Energy (Need for transition)
    {'source': 13, 'target': 11, 'strength': 0.5}, # Climate -> Cities (Resilience)
    {'source': 13, 'target': 14, 'strength': 0.8}, # Climate -> Life Below Water
    {'source': 13, 'target': 15, 'strength': 0.8}, # Climate -> Life on Land

    {'source': 16, 'target': 1, 'strength': 0.5},  # Peace/Justice -> Poverty
    {'source': 16, 'target': 8, 'strength': 0.6},  # Peace/Justice -> Decent Work
    {'source': 16, 'target': 10, 'strength': 0.7}, # Peace/Justice -> Inequality

    # Special handling for SDG 17 (Partnerships for the Goals)
    # target: -1 signifies a general positive influence on all other SDGs (1-16).
    # This is interpreted in the script to create individual relationships from 17 to each of 1-16.
    {'source': 17, 'target': -1, 'strength': 0.2} 
    # Add potential negative interactions / trade-offs if your bonus logic uses them.
    # Example: {'source': 7, 'target': 13, 'strength': -0.6}, # Fossil fuel energy conflicts with climate action
    # Example: {'source': 8, 'target': 15, 'strength': -0.5}, # Unsustainable growth conflicts with life on land
]

def populate_relationships():
    """
    Populates the `sdg_relationships` table with data from `RELATIONSHIP_DATA`.

    This function initializes the Flask application to establish an app context,
    allowing database operations. It checks if relationships already exist and
    skips population if the table is not empty. It validates SDG IDs against
    the `SdgGoal` table and handles a special case for SDG 17 to create
    relationships with all other SDGs. Uses `Decimal` for precision in 'strength'.
    Commits transactions on success, rolls back on error.
    """
    app = create_app() # Create an instance of the Flask application.
    # `app.app_context()` is essential for SQLAlchemy and other Flask extensions
    # to work correctly when the script is run outside of a typical request cycle.
    with app.app_context(): 
        print("Checking existing relationships...")
        # Query the database to see if any SdgRelationship records already exist.
        existing_count = db.session.query(SdgRelationship).count()

        if existing_count > 0:
            print(f"Database already contains {existing_count} relationships. Skipping population.")
            # Optional logic to clear existing relationships could be added here if re-population is desired.
            # Example:
            # db.session.query(SdgRelationship).delete()
            # db.session.commit()
            # print("Cleared existing relationships.")
            return # Exit if data already exists.

        print("Populating SDG relationships...")
        added_count = 0
        skipped_count = 0
        try:
            # Fetch all valid SDG IDs from the SdgGoal table once.
            # This set is used to validate source and target IDs in RELATIONSHIP_DATA.
            valid_sdg_ids = {goal.id for goal in db.session.query(SdgGoal.id).all()}

            for rel_data in RELATIONSHIP_DATA:
                source_id = rel_data['source']
                target_id = rel_data['target']
                # Convert strength to Decimal for precise storage, from string to avoid float inaccuracies.
                strength = Decimal(str(rel_data['strength'])) 

                # Special handling for SDG 17 (Partnerships for the Goals).
                # If source is 17 and target is -1, create relationships from SDG 17
                # to all other valid SDGs (1-16).
                if source_id == 17 and target_id == -1:
                    for actual_target_id in range(1, 17): # Assuming SDGs 1-16
                         # Check if this specific relationship (17 -> actual_target_id) already exists.
                         # This is good practice, though less critical if `existing_count` check at the start is done.
                         exists = db.session.query(SdgRelationship).filter_by(source_sdg_id=source_id, target_sdg_id=actual_target_id).first()
                         if not exists:
                             relationship = SdgRelationship(
                                 source_sdg_id=source_id,
                                 target_sdg_id=actual_target_id,
                                 strength=strength # Using 'strength' as per SdgRelationship model
                             )
                             db.session.add(relationship) # Add the new relationship to the session.
                             added_count += 1
                         else:
                            skipped_count +=1 # Count as skipped if it somehow already exists.
                # Standard relationship processing for other SDGs.
                elif source_id in valid_sdg_ids and target_id in valid_sdg_ids:
                     # Check if this specific relationship already exists.
                     exists = db.session.query(SdgRelationship).filter_by(source_sdg_id=source_id, target_sdg_id=target_id).first()
                     if not exists:
                        relationship = SdgRelationship(
                            source_sdg_id=source_id,
                            target_sdg_id=target_id,
                            strength=strength # Using 'strength' as per SdgRelationship model
                        )
                        db.session.add(relationship) # Add to session.
                        added_count += 1
                     else:
                        skipped_count += 1 # Count as skipped.
                else:
                    # Log a warning if source_id or target_id is not found in SdgGoal table.
                    print(f"  Warning: Skipping invalid relationship ({source_id} -> {target_id}). Check SDG IDs.")
                    skipped_count += 1

            db.session.commit() # Commit all added relationships to the database.
            print(f"Successfully added {added_count} new SDG relationships.")
            if skipped_count > 0:
                print(f"Skipped {skipped_count} relationships (duplicates or invalid IDs).")

        except Exception as e:
            db.session.rollback() # Rollback the transaction in case of any error.
            print(f"\nAn error occurred: {e}")
            print("Database transaction rolled back.")
        finally:
             # The application context is popped automatically when exiting the 'with' block.
             pass

# This block allows the script to be run directly from the command line (e.g., `python app/utils/populate_relationships.py`).
if __name__ == "__main__":
    print("Attempting to populate SDG relationships...")
    populate_relationships() # Call the main function to populate data.
    print("Script finished.")
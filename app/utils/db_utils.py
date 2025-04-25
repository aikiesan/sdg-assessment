# app/utils/db_utils.py
from flask import current_app
from app import db
from app.models.sdg import SdgGoal, SdgQuestion

SDG_GOAL_DATA = [
    {'number': 1, 'name': 'No Poverty', 'color_code': '#E5243B', 'description': 'End poverty...'},
    # ... all 17 goals (add the rest as needed)
]

def populate_goals():
    """Populates the sdg_goals table using SQLAlchemy session."""
    print("populate_goals: Starting...")
    added_count = 0
    try:
        for goal_data in SDG_GOAL_DATA:
            existing_goal = db.session.execute(db.select(SdgGoal).filter_by(number=goal_data['number'])).scalar_one_or_none()
            if not existing_goal:
                new_goal = SdgGoal(
                    number=goal_data['number'],
                    name=goal_data['name'],
                    color_code=goal_data['color_code'],
                    description=goal_data.get('description', '')
                )
                db.session.add(new_goal)
                added_count += 1
                print(f"  Adding SDG {goal_data['number']}...")

        if added_count > 0:
            print(f"populate_goals: Prepared {added_count} goals.")
        else:
            print("populate_goals: All goals already exist.")
        print("populate_goals: Succeeded.")
        return True
    except Exception as e:
        db.session.rollback()
        print(f"ERROR populating sdg_goals: {e}")
        print("populate_goals: Failed.")
        return False

def populate_questions():
    """Populates the sdg_questions table using SQLAlchemy session."""
    print("populate_questions: Starting...")
    added_count = 0
    final_success = False
    try:
        COL_ID = 'id'
        COL_TEXT = 'text'
        COL_TYPE = 'type'
        COL_SDG_ID = 'sdg_id'
        COL_MAX_SCORE = 'max_score'

        existing_ids = [q.id for q in db.session.execute(db.select(SdgQuestion.id)).scalars()]
        questions_to_add_data = []
        print(f"populate_questions: Existing IDs = {existing_ids}")

        for i in range(1, 32):
            if i not in existing_ids:
                target_sdg_id = ((i - 1) % 17) + 1
                q_type = 'checkbox' if i % 2 == 0 else 'radio'
                q_text = f'PLACEHOLDER TEXT: Question {i} (SDG {target_sdg_id})'
                q_max_score = 5.0
                questions_to_add_data.append({
                    COL_TEXT: q_text, COL_TYPE: q_type,
                    COL_SDG_ID: target_sdg_id, COL_MAX_SCORE: q_max_score,
                    'id': i
                })

        if not questions_to_add_data:
            print("populate_questions: No missing questions (1-31) found to add.")
            final_success = True
        else:
            print(f"populate_questions: Found {len(questions_to_add_data)} missing questions to add.")
            objects_to_add = []
            for q_data in questions_to_add_data:
                new_q = SdgQuestion(**q_data)
                objects_to_add.append(new_q)

            db.session.add_all(objects_to_add)
            print(f"populate_questions: Added {len(objects_to_add)} questions to session.")
            final_success = True

    except Exception as e:
        db.session.rollback()
        print(f"ERROR populating questions: {e}")
        final_success = False
    finally:
        if final_success:
            print("populate_questions: Succeeded.")
        else:
            print("populate_questions: Failed.")
    return final_success
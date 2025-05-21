"""
SDG Scoring Service.
This module contains the core logic for calculating Sustainable Development Goal (SDG)
scores based on question responses from assessments and considering inter-SDG
relationships (bonus/penalty system). It uses SQLAlchemy ORM for database
interactions in the primary scoring function and also includes helper functions,
some of which may still use raw SQL.
"""

import json
import math
# --- IMPORTS ---
# Note: Duplicate json and math imports were removed.
from app import db
from app.models.assessment import Assessment, SdgScore
from app.models.response import QuestionResponse # Used by calculate_sdg_scores
from app.models.sdg import SdgGoal, SdgQuestion
from app.models.sdg_relationship import SdgRelationship
from flask import current_app  # For logging

def map_option_to_score(option):
    """
    Maps a textual or numeric input option to a standardized numeric score.

    This function handles various input types:
    - None or empty strings map to 0.0.
    - Values that can be directly converted to float are returned as such.
    - Likert scale strings (e.g., 'strongly agree', 'neutral', 'disagree') are mapped to scores from 5.0 to 1.0.
    - Yes/No type strings (e.g., 'yes', 'no', 'true', 'false') are mapped to 5.0 or 0.0, with 'partially' as 3.0.
    - Other non-empty strings (often from checkboxes or unrecognized inputs) are given a default score.

    Args:
        option (str | int | float | None): The input option to map.

    Returns:
        float: The numeric score corresponding to the input option.
    """
    # Handle None or empty values
    if option is None or option == '':
        return 0.0
    # Handle already numeric values (e.g., if a score is directly provided)
    try:
        return float(option)
    except (ValueError, TypeError):
        # If not directly float, proceed to string mapping
        pass
    
    option_str = str(option).lower() # Convert to lowercase string for case-insensitive matching

    # Likert-type scales mapping
    if option_str in ('strongly agree', 'excellent', 'very high', 'always'):
        return 5.0
    elif option_str in ('agree', 'good', 'high', 'often'):
        return 4.0
    elif option_str in ('neutral', 'moderate', 'medium', 'sometimes'):
        return 3.0
    elif option_str in ('disagree', 'poor', 'low', 'rarely'):
        return 2.0
    elif option_str in ('strongly disagree', 'very poor', 'very low', 'never'):
        return 1.0
    # Yes/No type responses mapping
    elif option_str in ('yes', 'true', '1', 'y'):
        return 5.0
    elif option_str in ('partially', 'somewhat', 'in progress'): # Intermediate positive response
        return 3.0
    elif option_str in ('no', 'false', '0', 'n'):
        return 0.0
    
    # Checkbox/Unknown Value Handling:
    # If the option text doesn't match any known scale, it might be a checkbox value
    # (where the 'option' is the text of the checkbox itself if selected) or another
    # non-empty string. Assign a default positive score (e.g., 1.0) in such cases.
    # This assumes that any non-recognized, non-empty string implies a positive contribution.
    if option_str: # Any other non-empty string
        return 1.0 # Default score for unmatched, non-empty strings.
        
    # Default case if option_str is somehow empty after initial checks (should ideally not be reached)
    return 0.0


def calculate_sdg_scores(assessment_id):
    """
    Calculates direct, bonus, and total scores for each SDG within a given assessment,
    as well as the overall assessment score. This function uses SQLAlchemy ORM for all
    database interactions and updates Assessment and SdgScore records directly.

    The process involves:
    1. Fetching the assessment and performing initial checks (e.g., ensuring questions exist).
    2. Retrieving all question responses for the assessment.
    3. Calculating raw scores and maximum possible raw scores for each SDG based on responses.
    4. Normalizing these raw scores to a direct score (typically 0-10 scale), applying boosts or floors.
    5. Calculating bonus scores based on inter-SDG relationships (SdgRelationship) and direct scores of source SDGs.
    6. Summing direct and bonus scores to get total SDG scores, applying caps.
    7. Saving all calculated scores (raw, direct, bonus, total, percentage, question count) into SdgScore records.
    8. Calculating the overall assessment score as an average of total SDG scores and saving it to the Assessment record.

    Args:
        assessment_id (int): The ID of the assessment for which to calculate scores.

    Returns:
        dict: A dictionary containing the calculated total scores for each SDG
              (e.g., `{'sdg_scores': {1: 7.5, 2: 8.0, ...}, 'overall_score': 7.75}`)
              or an empty score set if critical errors occur.
    """
    # Extensive print statements are used for debugging. For production,
    # these should be replaced with current_app.logger.debug() or removed.
    # Example: current_app.logger.debug(f"--- ORM: ENTERING calculate_sdg_scores for assessment_id: {assessment_id} ---")
    print(f"--- ORM: ENTERING calculate_sdg_scores for assessment_id: {assessment_id} ---")

    # --- Fetching assessment and initial checks ---
    assessment = db.session.get(Assessment, assessment_id) # Fetch assessment by ID using ORM
    if not assessment:
        # current_app.logger.error(f"Assessment {assessment_id} not found via ORM.")
        print(f"ERROR: Assessment {assessment_id} not found via ORM.")
        return {'sdg_scores': {}, 'overall_score': 0}

    try:
        # Check if there are any questions defined in the system.
        question_count_db = db.session.query(SdgQuestion).count()
        if question_count_db == 0:
            # current_app.logger.critical("CRITICAL ERROR: sdg_questions table is empty or inaccessible (ORM query)!")
            print("CRITICAL ERROR: sdg_questions table is empty or inaccessible (ORM query)!")
            assessment.overall_score = 0 # Set overall score to 0
            db.session.commit() # Commit change to assessment
            return {'sdg_scores': {}, 'overall_score': 0}
        # current_app.logger.debug(f"ORM: Found {question_count_db} rows in sdg_questions table.")
        print(f"ORM: Found {question_count_db} rows in sdg_questions table.")
    except Exception as q_check_e:
        # current_app.logger.critical(f"CRITICAL ERROR checking sdg_questions table via ORM: {q_check_e}", exc_info=True)
        print(f"CRITICAL ERROR checking sdg_questions table via ORM: {q_check_e}")
        return {'sdg_scores': {}, 'overall_score': 0} # Return empty if cannot verify questions

    # --- Fetching QuestionResponse objects ---
    # current_app.logger.debug(f"ORM: Querying QuestionResponse for assessment_id = {assessment_id}")
    print(f"ORM: Querying QuestionResponse for assessment_id = {assessment_id}")
    try:
        # Retrieve all question responses for the given assessment.
        responses = QuestionResponse.query.filter_by(assessment_id=assessment_id).all()
    except Exception as query_e:
        # current_app.logger.critical(f"CRITICAL ERROR executing ORM query for responses: {query_e}", exc_info=True)
        print(f"CRITICAL ERROR executing ORM query for responses: {query_e}")
        assessment.overall_score = 0 # Set overall score to 0 on error
        db.session.commit() # Commit change
        return {'sdg_scores': {}, 'overall_score': 0}

    # Handle cases with no responses: initialize all SDG scores to 0.
    if not responses:
        # current_app.logger.info(f"ORM: Query returned 0 responses for assessment_id {assessment_id}. Initializing scores to 0.")
        print(f"ORM: Query returned 0 responses for assessment_id {assessment_id}.")
        assessment.overall_score = 0 # Set overall score to 0
        all_sdg_ids = [g.id for g in SdgGoal.query.all()] # Get all SDG IDs
        for sdg_id in all_sdg_ids:
            # Find existing or create new SdgScore record for each SDG.
            sdg_score_obj = SdgScore.query.filter_by(assessment_id=assessment_id, sdg_id=sdg_id).first()
            if not sdg_score_obj:
                sdg_score_obj = SdgScore(assessment_id=assessment_id, sdg_id=sdg_id)
                db.session.add(sdg_score_obj)
            # Set all score components to 0.
            sdg_score_obj.direct_score = 0.0
            sdg_score_obj.bonus_score = 0.0
            sdg_score_obj.total_score = 0.0
            sdg_score_obj.raw_score = 0.0
            sdg_score_obj.max_possible = 0.0
            sdg_score_obj.percentage_score = 0.0
            sdg_score_obj.question_count = 0
        db.session.commit() # Commit these zeroed scores.
        return {'sdg_scores': {}, 'overall_score': 0}

    # current_app.logger.debug(f"ORM: Query successfully found {len(responses)} responses.")
    print(f"ORM: Query successfully found {len(responses)} responses.")
    # current_app.logger.debug("First few responses fetched by ORM:")
    print("First few responses fetched by ORM:")
    for i, r in enumerate(responses[:5]):
        # current_app.logger.debug(f"  Row {i}: assessment={r.assessment_id}, q_id={r.question_id}, score={r.response_score}, text='{r.response_text}'")
        print(f"  Row {i}: assessment={r.assessment_id}, q_id={r.question_id}, score={r.response_score}, text='{r.response_text}'")

    # --- Raw Score Calculation Loop ---
    # current_app.logger.info("--- ORM: Starting Raw Score Calculation Loop ---")
    print("--- ORM: Starting Raw Score Calculation Loop ---")
    all_sdg_ids = [g.id for g in SdgGoal.query.all()] # List of all SDG IDs
    # Dictionaries to store aggregated raw scores, max possible scores, and question counts per SDG.
    sdg_raw_scores = {sdg_id: 0.0 for sdg_id in all_sdg_ids}
    sdg_max_possible_raw = {sdg_id: 0.0 for sdg_id in all_sdg_ids}
    sdg_question_counts = {sdg_id: 0 for sdg_id in all_sdg_ids}
    counted_questions_for_max = set() # To ensure max_score for a question is added only once per SDG.

    try:
        # Fetch details (sdg_id, max_score) for all questions in one go for efficiency.
        questions_details = {q.id: {'sdg_id': q.sdg_id, 'max_score': float(q.max_score or 5.0)} 
                             for q in SdgQuestion.query.all()}
    except Exception as q_details_e:
        # current_app.logger.error(f"ERROR fetching question details via ORM: {q_details_e}", exc_info=True)
        print(f"ERROR fetching question details via ORM: {q_details_e}")
        return {'sdg_scores': {}, 'overall_score': 0}

    # Iterate through each response to aggregate scores.
    for response in responses:
        question_id = response.question_id
        response_score = float(response.response_score or 0.0) # Actual score achieved for the response.
        
        q_detail = questions_details.get(question_id) # Get pre-fetched question details.
        if not q_detail:
            # current_app.logger.warning(f"  Details not found for Question ID {question_id}. Skipping response.")
            print(f"  Warning: Details not found for Question ID {question_id}. Skipping response.")
            continue
        
        sdg_id = q_detail['sdg_id'] # SDG this question belongs to.
        # current_app.logger.debug(f"  ORM Processing response: Q_ID={question_id}, SDG_ID={sdg_id}, Score={response_score}")
        print(f"  ORM Processing response: Q_ID={question_id}, SDG_ID={sdg_id}, Score={response_score}")
        
        if sdg_id not in sdg_raw_scores: # Should not happen if all_sdg_ids is comprehensive
            # current_app.logger.warning(f"  Warning: SDG ID {sdg_id} from question details not in goal list. Skipping.")
            print(f"  Warning: SDG ID {sdg_id} from question details not in goal list. Skipping.")
            continue
            
        sdg_raw_scores[sdg_id] += response_score # Accumulate raw score for the SDG.
        sdg_question_counts[sdg_id] += 1 # Increment question count for the SDG.
        
        # Add to max possible score for the SDG, ensuring each question's max score is added only once.
        if question_id not in counted_questions_for_max:
            q_max_score = q_detail.get('max_score', 5.0) # Default max_score if not specified.
            sdg_max_possible_raw[sdg_id] += q_max_score
            counted_questions_for_max.add(question_id)
            # current_app.logger.debug(f"    -> Added max score {q_max_score} for Q{question_id} to SDG {sdg_id}. New Max Total: {sdg_max_possible_raw[sdg_id]}")
            print(f"    -> Added max score {q_max_score} for Q{question_id} to SDG {sdg_id}. New Max Total: {sdg_max_possible_raw[sdg_id]}")
        # current_app.logger.debug(f"    -> SDG {sdg_id}: New Raw Score = {sdg_raw_scores[sdg_id]}, Count = {sdg_question_counts[sdg_id]}")
        print(f"    -> SDG {sdg_id}: New Raw Score = {sdg_raw_scores[sdg_id]}, Count = {sdg_question_counts[sdg_id]}")

    # current_app.logger.info("--- ORM: Finished Raw Score Calculation Loop ---")
    print("--- ORM: Finished Raw Score Calculation Loop ---")
    
    # --- Normalized Scores Calculation ---
    # current_app.logger.info("--- ORM: Calculating Normalized Scores ---")
    print("--- ORM: Calculating Normalized Scores ---")
    sdg_direct_scores = {} # Stores the normalized direct score for each SDG.
    for sdg_id in all_sdg_ids:
        raw_score = sdg_raw_scores.get(sdg_id, 0)
        max_possible = sdg_max_possible_raw.get(sdg_id, 0)
        q_count = sdg_question_counts.get(sdg_id, 0)
        # current_app.logger.debug(f"SDG {sdg_id}: Raw={raw_score}, MaxPossible={max_possible}, QuestionCount={q_count}")
        print(f"SDG {sdg_id}: Raw={raw_score}, MaxPossible={max_possible}, QuestionCount={q_count}")
        
        if max_possible > 0:
            # Initial normalization: (raw_score / max_possible) * 10.
            # Boost: A 1.25 multiplier is applied to potentially raise scores, capped at 10.
            normalized_score = min(10, (raw_score / max_possible) * 10 * 1.25)

            # Floor adjustment: If any response contributed (raw_score > 0) but normalized score is below 3.0, set to 3.0.
            if raw_score > 0 and normalized_score < 3.0:
                normalized_score = 3.0
                # current_app.logger.debug(f"  Applied minimum score floor of 3.0 for SDG {sdg_id}")
                print(f"  Applied minimum score floor of 3.0 for SDG {sdg_id}")

            # Progressive scaling for mid-range scores (3.0 to < 7.0).
            # Scores in this range are scaled up to make improvements feel more significant.
            if 3.0 <= normalized_score < 7.0:
                original_score = normalized_score
                # The portion of the score above 3.0 is multiplied by 1.2.
                normalized_score = 3.0 + (normalized_score - 3.0) * 1.2
                # current_app.logger.debug(f"  Applied progressive scaling to SDG {sdg_id}: {original_score:.2f} -> {normalized_score:.2f}")
                print(f"  Applied progressive scaling to SDG {sdg_id}: {original_score:.2f} -> {normalized_score:.2f}")
        else:
            normalized_score = 0 # No questions or max_possible is 0 for this SDG.
            
        sdg_direct_scores[sdg_id] = normalized_score
        # current_app.logger.debug(f"  -> NormalizedDirect={normalized_score:.2f}")
        print(f"  -> NormalizedDirect={normalized_score:.2f}")

    # --- Bonus Scores Calculation ---
    current_app.logger.info("--- ORM: Calculating Bonus Scores ---")
    sdg_bonus_scores = {sdg_id: 0.0 for sdg_id in all_sdg_ids} # Initialize all bonus scores to 0.

    try:
        # Fetch all SDG relationships from the database.
        all_relationships = SdgRelationship.query.all()
        if not all_relationships:
            current_app.logger.warning("ORM WARNING: No SDG relationships found. Bonus scores will remain 0.")
        else:
            current_app.logger.info(f"ORM: Found {len(all_relationships)} SDG relationships.")

            # Iterate through each relationship to calculate potential bonus.
            for rel in all_relationships:
                source_sdg_id = rel.source_sdg_id
                target_sdg_id = rel.target_sdg_id
                strength = float(rel.strength or 0.0) # Relationship strength (positive for synergy).

                if target_sdg_id not in sdg_bonus_scores: # Should not happen if all_sdg_ids is correct.
                    current_app.logger.warning(f"  Skipping relationship: Target SDG {target_sdg_id} not in score dictionary.")
                    continue

                source_direct_score = sdg_direct_scores.get(source_sdg_id, 0.0) # Get direct score of the source SDG.

                # Bonus Logic: Apply bonus if source SDG score is high (>= 6.0) and relationship is positive.
                bonus_increment = 0.0
                if source_direct_score >= 6.0 and strength > 0:
                    threshold = 6.0 # Min score for source SDG to generate bonus.
                    factor = 0.15   # Tunable factor for bonus magnitude.
                    # Bonus is proportional to how much source score exceeds threshold, relationship strength, and factor.
                    bonus_increment = (source_direct_score - threshold) * strength * factor
                    sdg_bonus_scores[target_sdg_id] += bonus_increment # Add to target SDG's bonus.
                    current_app.logger.debug(f"  Applying bonus to SDG {target_sdg_id}: +{bonus_increment:.2f} (From SDG {source_sdg_id}, Score: {source_direct_score:.1f}, Strength: {strength:.2f})")

            # Bonus Cap: Limit the maximum bonus points an SDG can receive.
            MAX_BONUS_POINTS = 2.0 
            for sdg_id in sdg_bonus_scores:
                original_bonus = sdg_bonus_scores[sdg_id]
                # Ensure bonus is not negative and does not exceed MAX_BONUS_POINTS.
                capped_bonus = min(max(original_bonus, 0.0), MAX_BONUS_POINTS)
                sdg_bonus_scores[sdg_id] = capped_bonus
                if original_bonus != capped_bonus and original_bonus > 0:
                    current_app.logger.info(f"  Capped Bonus for SDG {sdg_id}: {original_bonus:.2f} -> {capped_bonus:.2f}")

    except Exception as bonus_calc_e:
        current_app.logger.error(f"ERROR during bonus score calculation: {bonus_calc_e}", exc_info=True)
        # Fallback to 0 bonus for all SDGs if an error occurs during calculation.
        sdg_bonus_scores = {sdg_id: 0.0 for sdg_id in all_sdg_ids}
        
    # --- Total Scores Calculation ---
    current_app.logger.info("--- ORM: Calculating Total Scores ---")
    sdg_total_scores = {} # Stores final total score for each SDG.
    for sdg_id in all_sdg_ids:
        direct = sdg_direct_scores.get(sdg_id, 0.0)
        bonus = sdg_bonus_scores.get(sdg_id, 0.0) # Use calculated and capped bonus.
        total = direct + bonus
        # Cap total score between 0 and 10.
        sdg_total_scores[sdg_id] = min(max(total, 0.0), 10.0)
        current_app.logger.debug(f"SDG {sdg_id}: Direct={direct:.2f}, Bonus={bonus:.2f}, Raw Total={total:.2f}, Final Total Score = {sdg_total_scores[sdg_id]:.2f}")

    # --- Saving Calculated Scores to SdgScore table ---
    current_app.logger.info("--- ORM: Saving Calculated Scores to sdg_scores table ---")
    for sdg_id in all_sdg_ids:
        # Fetch existing SdgScore object or create a new one if it doesn't exist.
        sdg_score_obj = SdgScore.query.filter_by(assessment_id=assessment_id, sdg_id=sdg_id).first()
        if not sdg_score_obj:
            sdg_score_obj = SdgScore(assessment_id=assessment_id, sdg_id=sdg_id)
            db.session.add(sdg_score_obj) # Add new SdgScore object to session.

        # Assign all calculated values to the SdgScore object.
        direct_score_val = sdg_direct_scores.get(sdg_id, 0.0)
        bonus_score_val = sdg_bonus_scores.get(sdg_id, 0.0)
        total_score_val = sdg_total_scores.get(sdg_id, 0.0)
        raw_score_val = sdg_raw_scores.get(sdg_id, 0.0)
        max_possible_val = sdg_max_possible_raw.get(sdg_id, 0.0)
        percentage_val = (raw_score_val / max_possible_val) * 100 if max_possible_val > 0 else 0.0
        question_count_val = sdg_question_counts.get(sdg_id, 0)

        sdg_score_obj.direct_score = direct_score_val
        sdg_score_obj.bonus_score = bonus_score_val
        sdg_score_obj.total_score = total_score_val
        sdg_score_obj.raw_score = raw_score_val
        sdg_score_obj.max_possible = max_possible_val
        sdg_score_obj.percentage_score = percentage_val
        sdg_score_obj.question_count = question_count_val

        current_app.logger.debug(f"  ORM Preparing to Save SDG {sdg_id}: Direct={sdg_score_obj.direct_score:.2f}, Bonus={sdg_score_obj.bonus_score:.2f}, Total={sdg_score_obj.total_score:.2f}, Count={sdg_score_obj.question_count}")

    # --- Overall Score Calculation and Saving ---
    # current_app.logger.info("--- ORM: Calculating and Saving Overall Score ---")
    print("--- ORM: Calculating and Saving Overall Score ---")
    # Calculate overall score as the average of valid total SDG scores.
    valid_total_scores = [score for score in sdg_total_scores.values() if score is not None]
    overall_score = sum(valid_total_scores) / len(valid_total_scores) if valid_total_scores else 0
    overall_score = round(overall_score, 2) # Round to two decimal places.
    # current_app.logger.info(f"ORM Calculated Overall Score: {overall_score}")
    print(f"ORM Calculated Overall Score: {overall_score}")
    
    # Update the assessment's overall score and updated_at timestamp.
    assessment.overall_score = overall_score
    assessment.updated_at = db.func.now() # Use database's current time function.
    
    try:
        db.session.commit() # Commit all changes to the database (SdgScore updates, Assessment update).
        # current_app.logger.info("--- ORM: Committed sdg_scores updates and assessment overall_score ---")
        print("--- ORM: Committed sdg_scores updates and assessment overall_score ---")
    except Exception as final_commit_e:
        db.session.rollback() # Rollback transaction on final commit error.
        # current_app.logger.error(f"ERROR during final commit in scoring service: {final_commit_e}", exc_info=True)
        print(f"ERROR during final commit in scoring service: {final_commit_e}")
        return {'sdg_scores': {}, 'overall_score': 0} # Return empty on error.
        
    # current_app.logger.info(f"--- ORM: EXITING calculate_sdg_scores for assessment_id: {assessment_id} ---")
    print(f"--- ORM: EXITING calculate_sdg_scores for assessment_id: {assessment_id} ---")
    return {'sdg_scores': sdg_total_scores, 'overall_score': overall_score}


# --- Start of commented-out raw SQL version ---
# The following block of code appears to be an older version of score calculation
# using raw SQL queries. It is currently commented out and seems to be superseded
# by the ORM-based `calculate_sdg_scores` function above.
# If this raw SQL version is no longer needed and the ORM version is fully functional
# and preferred, this block should be removed to reduce code clutter and maintainability.
# TODO: Confirm if this raw SQL block is entirely obsolete and can be deleted.
"""
    if not questions:
        print("Warning: No questions found in the database.")
        # Set overall score to 0 in assessment table if no questions exist
        conn.execute('UPDATE assessments SET overall_score = 0, updated_at = CURRENT_TIMESTAMP WHERE id = ?', (assessment_id,))
        return {'sdg_scores': {}, 'overall_score': 0}

    questions_dict = {q['id']: dict(q) for q in questions}

    # Get all question responses for this assessment
    responses = conn.execute('''
        SELECT * FROM question_responses
        WHERE assessment_id = ?
    ''', (assessment_id,)).fetchall()
    if not responses:
        print(f"Warning: No responses found for assessment_id {assessment_id}.")
        # Proceed to calculate 0 scores for all SDGs

    # Create a lookup dictionary of responses by question ID
    response_lookup = {r['question_id']: r for r in responses}

    # --- Step 1: Calculate Raw Scores and Max Possible Raw Scores per SDG ---
    all_sdg_ids = [q['id'] for q in conn.execute('SELECT id FROM sdg_goals').fetchall()]
    sdg_raw_scores = {}
    sdg_max_possible_raw = {}
    sdg_question_counts = {sdg_id: 0 for sdg_id in all_sdg_ids}

    for sdg_id in all_sdg_ids:  # Initialize all SDGs
        sdg_raw_scores[sdg_id] = 0
        sdg_max_possible_raw[sdg_id] = 0

    for qid, question_info in questions_dict.items():
        sdg_id = question_info['sdg_id']
        if sdg_id not in all_sdg_ids: continue  # Skip if somehow question maps to non-existent SDG

        # Add max possible score for this question (typically 5)
        q_max_score = float(question_info.get('max_score', 5))
        sdg_max_possible_raw[sdg_id] += q_max_score
        sdg_question_counts[sdg_id] += 1  # Count questions per SDG

        # Add actual score achieved for this question from responses
        response = response_lookup.get(qid)
        if response:
            sdg_raw_scores[sdg_id] += response['response_score']

    # --- Step 2: Calculate Normalized Direct Scores (0-10 scale) ---
    sdg_direct_scores = {}
    for sdg_id in all_sdg_ids:
        raw_score = sdg_raw_scores.get(sdg_id, 0)
        max_possible = sdg_max_possible_raw.get(sdg_id, 0)

        if max_possible > 0:
            # Enhanced normalization formula with a more significant boost
            # This applies a 25% boost to scores to counteract the feeling of scores being lowered
            normalized_score = min(10, (raw_score / max_possible) * 10 * 1.25)
            
            # Apply a floor of 4.0 for any SDG that has at least one response
            if raw_score > 0 and normalized_score < 4.0:
                normalized_score = 4.0
                print(f"  Applied minimum score floor of 4.0 for SDG {sdg_id}")
            
            # Apply progressive scaling to mid-range scores to make them feel more rewarding
            # This creates a more generous curve in the middle range (4-7)
            if 4.0 <= normalized_score < 7.0:
                original_score = normalized_score
                normalized_score = 4.0 + (normalized_score - 4.0) * 1.2
                print(f"  Applied progressive scaling to SDG {sdg_id}: {original_score:.2f} -> {normalized_score:.2f}")
        else:
            normalized_score = 0  # Assign 0 if no questions/max score defined for this SDG

        sdg_direct_scores[sdg_id] = normalized_score
        print(f"SDG ID {sdg_id}: Raw={raw_score}, MaxPossible={max_possible}, NormalizedDirect={normalized_score:.2f}")  # Debug print

    # --- Step 3: Calculate Bonus Scores (Cross-SDG Point Transfer) ---
    relationships = conn.execute('SELECT * FROM sdg_relationships').fetchall()
    sdg_relationships = {}
    
    # Debug: Check if relationships data exists
    if not relationships:
        print("WARNING: No SDG relationships found in the database. Cross-SDG Point Transfer will not work.")
    else:
        print(f"Found {len(relationships)} SDG relationships in the database.")
    
    for rel in relationships:
        source_id = rel['source_sdg_id']
        if source_id not in sdg_relationships: sdg_relationships[source_id] = []
        sdg_relationships[source_id].append({
            'target_id': rel['target_sdg_id'],
            'strength': rel['relationship_strength']
        })

    sdg_bonus_scores = {sdg_id: 0 for sdg_id in all_sdg_ids}
    for source_id, direct_score in sdg_direct_scores.items():
        # Lower the threshold for bonus point generation from 7 to 6
        # This allows more SDGs to generate bonus points
        if direct_score >= 6:
            bonus_value = 0
            if direct_score >= 9: bonus_value = 1.5    # Increased from 1.0
            elif direct_score >= 8: bonus_value = 1.0  # Increased from 0.7
            elif direct_score >= 7: bonus_value = 0.7  # Increased from 0.5
            else: bonus_value = 0.5                    # New tier for scores >=6
            
            print(f"SDG {source_id} has direct score {direct_score:.2f} >= 6, generating bonus value: {bonus_value}")

            if source_id in sdg_relationships:
                sorted_relations = sorted(sdg_relationships[source_id], key=lambda x: x['strength'], reverse=True)
                print(f"  Found {len(sorted_relations)} relationships for SDG {source_id}")
                
                # Increase from top 3 to top 4 relationships
                for relation in sorted_relations[:4]:
                    target_id = relation['target_id']
                    strength = relation['strength']
                    if target_id in sdg_bonus_scores:  # Check if target SDG exists
                        bonus = bonus_value * strength
                        sdg_bonus_scores[target_id] += bonus
                        print(f"  Applying bonus from SDG {source_id} to SDG {target_id}: +{bonus:.2f} (Strength: {strength}, Base: {bonus_value})")
            else:
                print(f"  No relationships found for SDG {source_id}")

    # Apply balance constraint: Max 3 bonus points receivable per SDG (increased from 2)
    for sdg_id in sdg_bonus_scores:
        original_bonus = sdg_bonus_scores[sdg_id]
        sdg_bonus_scores[sdg_id] = min(original_bonus, 3)
        if original_bonus > 0:
            print(f"SDG {sdg_id} bonus points: {original_bonus:.2f}, after cap: {sdg_bonus_scores[sdg_id]:.2f}")

    # --- Step 4: Calculate Total Scores (Direct + Bonus, capped at 10) ---
    sdg_total_scores = {}
    for sdg_id in all_sdg_ids:
        direct = sdg_direct_scores.get(sdg_id, 0)
        bonus = sdg_bonus_scores.get(sdg_id, 0)
        total = direct + bonus
        sdg_total_scores[sdg_id] = min(total, 10)  # Cap total score at 10

    # --- Step 5: Store Detailed Scores in Database ---
    for sdg_id in all_sdg_ids:
        direct_score_val = sdg_direct_scores.get(sdg_id, 0)
        bonus_score_val = sdg_bonus_scores.get(sdg_id, 0)
        raw_score_val = sdg_raw_scores.get(sdg_id, 0)
        max_possible_val = sdg_max_possible_raw.get(sdg_id, 0)
        total_score_val = min(direct_score_val + bonus_score_val, 10)
        percentage_val = (raw_score_val / max_possible_val) * 100 if max_possible_val > 0 else 0
        question_count_val = sdg_question_counts.get(sdg_id, 0)

        print(f"DEBUG Scoring Service: Preparing to save for SDG {sdg_id}: Direct={direct_score_val:.2f}, Bonus={bonus_score_val:.2f}, Total={total_score_val:.2f}, Raw={raw_score_val}, Max={max_possible_val}, Percentage={percentage_val:.2f}, Count={question_count_val}")

        existing = conn.execute('SELECT id FROM sdg_scores WHERE assessment_id = ? AND sdg_id = ?', (assessment_id, sdg_id)).fetchone()

        if existing:
            conn.execute('''
                UPDATE sdg_scores SET
                    direct_score = ?, bonus_score = ?, total_score = ?,
                    raw_score = ?, max_possible = ?, percentage_score = ?, question_count = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (direct_score_val, bonus_score_val, total_score_val,
                  raw_score_val, max_possible_val, percentage_val, question_count_val,
                  existing['id']))
        else:
            conn.execute('''
                INSERT INTO sdg_scores (
                    assessment_id, sdg_id, direct_score, bonus_score, total_score,
                    raw_score, max_possible, percentage_score, question_count,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            ''', (assessment_id, sdg_id, direct_score_val, bonus_score_val, total_score_val,
                  raw_score_val, max_possible_val, percentage_val, question_count_val))

    # --- Step 6: Calculate and Update Overall Assessment Score ---
    valid_total_scores = [score for score in sdg_total_scores.values() if score is not None]
    overall_score = sum(valid_total_scores) / len(valid_total_scores) if valid_total_scores else 0
    overall_score = round(overall_score, 2)
    print(f"Calculated Overall Score: {overall_score}")  # Debug print

    conn.execute('''
        UPDATE assessments SET overall_score = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?
    ''', (overall_score, assessment_id))

    # Note: No commit here, commit happens in the calling function

    return {
        'sdg_scores': sdg_total_scores,
        'overall_score': overall_score
    }
"""
# --- End of commented-out raw SQL version ---

def process_question_response(question_type, value, options=None, max_score=5):
    """
    Processes a single question's response and calculates its raw score based on question type.

    This function is typically called when initially processing form data before
    it's stored in the `QuestionResponse` model or when needing to re-evaluate
    a raw response score.
    
    Args:
        question_type (str): The type of question (e.g., 'select', 'checklist').
        value (str | list | dict): The response value from the form/input.
                                   For 'checklist', this might be a JSON string of selected keys or a list.
        options (str | list | dict, optional): Question options, primarily for 'checklist'.
                                               Can be a JSON string of options or parsed structure.
                                               Each option can have a 'key' and 'value' (score).
        max_score (float | int): The maximum possible score for this question.
        
    Returns:
        float: The calculated raw score for the response, capped by `max_score`.
    """
    # For 'select' or radio button type questions, the value itself is often the score.
    if question_type == 'select':
        try:
            # Ensure the value is a float and does not exceed max_score.
            return min(float(value), float(max_score))
        except (ValueError, TypeError):
            return 0.0 # Return 0 if value cannot be converted to float.
    
    # For 'checklist' type questions, sum scores of selected options.
    elif question_type == 'checklist':
        try:
            # `value` might be a JSON string of selected keys or already a list.
            selected_keys = json.loads(value) if isinstance(value, str) else value
            
            if not selected_keys or not isinstance(selected_keys, list):
                return 0.0 # No valid selections.
            
            current_score = 0.0
            # If specific options with scores are provided:
            if options:
                try:
                    # `options` might be a JSON string or already parsed.
                    options_data = json.loads(options) if isinstance(options, str) else options
                    # Create a map of option key/text to its score value.
                    option_value_map = {opt.get('key', opt['text']): float(opt.get('value', 1)) 
                                       for opt in options_data}
                    
                    # Sum scores for selected keys.
                    current_score = sum(option_value_map.get(key, 0) for key in selected_keys)
                except (json.JSONDecodeError, KeyError, TypeError, ValueError) as e:
                    # current_app.logger.warning(f"Error parsing checklist options or values: {e}. Falling back to 1 point per selection.")
                    # Fallback: if options parsing fails, count 1 point per selected item.
                    current_score = float(len(selected_keys))
            else:
                # No options with specific scores defined, count 1 point per selected item.
                current_score = float(len(selected_keys))
            
            # Example of commented-out special handling:
            # if question_id in [29, 30, 31]:
            #     if len(selected_keys) > 0:
            #         min_score = len(selected_keys) * 0.75
            #         current_score = max(current_score, min_score)
            
            return min(current_score, float(max_score)) # Ensure score does not exceed max_score.
        
        except (json.JSONDecodeError, TypeError):
            # Error in parsing `value` as JSON or if `value` is not a list after parsing.
            return 0.0
    
    # Default for other question types or if errors occur.
    return 0.0

# TODO: Refactor this function to use SQLAlchemy ORM for consistency and better database interaction.
def get_assessment_summary(conn, assessment_id):
    """
    Generates a summary of assessment results for display purposes.
    This function currently uses raw SQL queries via a passed database connection (`conn`).

    Args:
        conn: A database connection object (e.g., from `app.utils.db.get_db()`).
        assessment_id (int): The ID of the assessment to summarize.
        
    Returns:
        dict: A dictionary containing various summary components like assessment details,
              SDG scores, category breakdowns, top/bottom SDGs, and chart data.
              Returns `{'error': 'Assessment not found'}` if the assessment does not exist.
    """
    # Get assessment details along with project name and description using a JOIN.
    # This is a raw SQL query.
    assessment_data = conn.execute('''
        SELECT a.*, p.name as project_name, p.description as project_description
        FROM assessments a
        JOIN projects p ON a.project_id = p.id
        WHERE a.id = ?
    ''', (assessment_id,)).fetchone()
    
    if not assessment_data:
        return {'error': 'Assessment not found'} # Handle case where assessment_id is invalid.
    
    # Get all SDG scores for this assessment, joined with SDG goal details.
    # This is a raw SQL query.
    scores_data = conn.execute('''
        SELECT s.*, g.number, g.name, g.description, g.color_code
        FROM sdg_scores s
        JOIN sdg_goals g ON s.sdg_id = g.id
        WHERE s.assessment_id = ?
        ORDER BY g.number
    ''', (assessment_id,)).fetchall()
    
    # Convert SQL row objects to a list of dictionaries for easier processing and JSON serialization.
    scores_list = [dict(score_row) for score_row in scores_data]
    
    # Group scores by predefined SDG categories.
    # This categorization is hardcoded here.
    categories = {
        'People': [s for s in scores_list if s['number'] in [1, 2, 3, 4, 5]],
        'Planet': [s for s in scores_list if s['number'] in [6, 12, 13, 14, 15]],
        'Prosperity': [s for s in scores_list if s['number'] in [7, 8, 9, 10, 11]],
        'Peace & Partnership': [s for s in scores_list if s['number'] in [16, 17]]
    }
    
    # Calculate average scores for each category.
    category_average_scores = {}
    for category_name, scores_in_category in categories.items():
        if scores_in_category:
            category_average_scores[category_name] = sum(s['total_score'] for s in scores_in_category) / len(scores_in_category)
        else:
            category_average_scores[category_name] = 0.0 # Default to 0 if no scores in category.
    
    # Identify top 3 and bottom 3 performing SDGs based on total_score.
    sorted_scores = sorted(scores_list, key=lambda s: s['total_score'], reverse=True)
    top_sdgs = sorted_scores[:3] # Top 3 (or fewer if less than 3 SDGs).
    bottom_sdgs = sorted_scores[-3:] if len(sorted_scores) >=3 else sorted_scores # Bottom 3 (or fewer). Note: this will be in ascending order of score.
    
    # Prepare data formatted for chart generation (e.g., bar chart of scores).
    chart_data = [
        {
            'sdg': score['number'],
            'name': score['name'],
            'direct': score['direct_score'],
            'bonus': score['bonus_score'],
            'total': score['total_score'],
            'color': score['color_code']
        }
        for score in scores_list
    ]
    
    # Compile the summary dictionary.
    return {
        'assessment': dict(assessment_data), # Overall assessment details.
        'scores': scores_list,               # List of all SDG scores.
        'categories': categories,            # Scores grouped by category.
        'category_scores': category_average_scores, # Average score per category.
        'top_sdgs': top_sdgs,                # Top performing SDGs.
        'bottom_sdgs': bottom_sdgs,          # Bottom performing SDGs.
        'chart_data': chart_data,            # Data formatted for charts.
        'overall_score': assessment_data['overall_score'] # Overall assessment score.
    }

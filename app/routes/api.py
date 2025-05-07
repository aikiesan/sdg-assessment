"""
API routes for the application.
Provides JSON endpoints for AJAX requests and external integrations.
"""

import jwt as pyjwt
print("PYJWT MODULE PATH:", pyjwt.__file__)
import datetime
from flask import Blueprint, jsonify, request, session, current_app
from flask import g
from app.utils.auth import token_required
from werkzeug.security import check_password_hash
from app.utils.db import get_db
from app.services.scoring_service import get_assessment_summary
import json

api_bp = Blueprint('api', __name__)

@api_bp.route('/v1/auth/login', methods=['POST'])
def api_login():
    data = request.get_json()
    if not data or 'email' not in data or 'password' not in data:
        return jsonify({'error': 'Missing email or password'}), 400
    
    email = data.get('email')
    password = data.get('password')
    
    conn = get_db()
    user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
    
    if user and check_password_hash(user['password_hash'], password):
        # Gerar JWT token
        token = pyjwt.encode(
            {
                'user_id': user['id'],
                'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
            },
            current_app.config['SECRET_KEY'],
            algorithm='HS256'
        )
        return jsonify({'token': token, 'user_id': user['id']}), 200
    
    return jsonify({'error': 'Invalid credentials'}), 401

@api_bp.route('/v1/projects', methods=['GET', 'POST'])
@token_required
def projects_handler():
    """GET: List all projects for the user. POST: Create a project."""
    user_id = g.user_id
    conn = get_db()
    if request.method == 'POST':
        data = request.get_json() or {}
        name = data.get('name')
        if not name:
            return jsonify({'error': 'Project name is required'}), 400
        description = data.get('description')
        project_type = data.get('project_type')
        location = data.get('location')
        size_sqm = data.get('size_sqm')
        cur = conn.execute('''
            INSERT INTO projects (name, description, project_type, location, size_sqm, user_id, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        ''', (name, description, project_type, location, size_sqm, user_id))
        conn.commit()
        project_id = cur.lastrowid
        project = conn.execute('SELECT * FROM projects WHERE id = ?', (project_id,)).fetchone()
        return jsonify(dict(project)), 201
    # GET
    projects = conn.execute('''
        SELECT p.*, (
            SELECT COUNT(*) FROM assessments a WHERE a.project_id = p.id
        ) AS assessment_count
        FROM projects p
        WHERE p.user_id = ?
        ORDER BY p.updated_at DESC
    ''', (user_id,)).fetchall()
    projects_list = [dict(project) for project in projects]
    return jsonify(projects_list)

@api_bp.route('/v1/projects/<int:project_id>', methods=['GET', 'PUT', 'DELETE'])
@token_required
def project_detail_handler(project_id):
    """GET: Get project. PUT: Update project. DELETE: Delete project."""
    user_id = g.user_id
    conn = get_db()
    project = conn.execute('SELECT * FROM projects WHERE id = ? AND user_id = ?', (project_id, user_id)).fetchone()
    if not project:
        return jsonify({'error': 'Project not found'}), 404
    if request.method == 'PUT':
        data = request.get_json() or {}
        name = data.get('name')
        description = data.get('description')
        project_type = data.get('project_type')
        location = data.get('location')
        size_sqm = data.get('size_sqm')
        conn.execute('''
            UPDATE projects SET name = ?, description = ?, project_type = ?, location = ?, size_sqm = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ? AND user_id = ?
        ''', (name, description, project_type, location, size_sqm, project_id, user_id))
        conn.commit()
        updated_project = conn.execute('SELECT * FROM projects WHERE id = ?', (project_id,)).fetchone()
        return jsonify(dict(updated_project)), 200
    elif request.method == 'DELETE':
        conn.execute('DELETE FROM projects WHERE id = ? AND user_id = ?', (project_id, user_id))
        conn.commit()
        return '', 204
    # GET
    assessments = conn.execute('''
        SELECT * FROM assessments 
        WHERE project_id = ? 
        ORDER BY created_at DESC
    ''', (project_id,)).fetchall()
    project_dict = dict(project)
    assessments_list = [dict(assessment) for assessment in assessments]
    project_dict['assessments'] = assessments_list
    return jsonify(project_dict)

@api_bp.route('/v1/projects/<int:project_id>/assessments', methods=['POST'])
@token_required
def create_project_assessment(project_id):
    user_id = g.user_id
    conn = get_db()
    project = conn.execute('SELECT * FROM projects WHERE id = ? AND user_id = ?', (project_id, user_id)).fetchone()
    if not project:
        return jsonify({'error': 'Project not found'}), 404
    data = request.get_json() or {}
    name = data.get('name', 'Assessment')
    # Create new assessment
    conn.execute('''
        INSERT INTO assessments (project_id, user_id, status, created_at, updated_at)
        VALUES (?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
    ''', (project_id, user_id, 'draft'))
    conn.commit()
    new_assessment_id = conn.execute('SELECT last_insert_rowid()').fetchone()[0]
    new_assessment = conn.execute('SELECT * FROM assessments WHERE id = ?', (new_assessment_id,)).fetchone()
    if new_assessment:
        response_data = dict(new_assessment)
        response_data['name'] = name
        return jsonify(response_data), 201
    else:
        return jsonify({'error': 'Failed to retrieve created assessment'}), 500


@api_bp.route('/v1/assessments/<int:assessment_id>/finalize', methods=['POST'])
@token_required
def finalize_assessment_api(assessment_id):
    user_id = g.user_id
    conn = get_db()
    assessment = conn.execute('''
        SELECT a.*, p.user_id FROM assessments a JOIN projects p ON a.project_id = p.id WHERE a.id = ?
    ''', (assessment_id,)).fetchone()
    if not assessment or assessment['user_id'] != user_id:
        return jsonify({'error': 'Assessment not found'}), 404
    # Mark assessment as completed
    conn.execute('''
        UPDATE assessments SET status = ?, completed_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP WHERE id = ?
    ''', ('completed', assessment_id))
    conn.commit()
    overall_score = 100  # Placeholder
    return jsonify({'message': 'Assessment finalized successfully', 'overall_score': overall_score, 'status': 'completed'}), 200




@api_bp.route('/v1/assessments/<int:assessment_id>', methods=['GET'])
@token_required
def get_assessment(assessment_id):
    """Get a specific assessment by ID."""
    user_id = g.user_id
    
    conn = get_db()
    assessment = conn.execute('''
        SELECT a.*, p.name as project_name
        FROM assessments a
        JOIN projects p ON a.project_id = p.id
        WHERE a.id = ? AND p.user_id = ?
    ''', (assessment_id, user_id)).fetchone()
    
    if not assessment:
        return jsonify({'error': 'Assessment not found or access denied'}), 404
    
    # Get SDG scores
    scores = conn.execute('''
        SELECT s.*, g.number, g.name, g.description, g.color_code
        FROM sdg_scores s
        JOIN sdg_goals g ON s.sdg_id = g.id
        WHERE s.assessment_id = ?
        ORDER BY g.number
    ''', (assessment_id,)).fetchall()
    
    assessment_dict = dict(assessment)
    assessment_dict['scores'] = [dict(s) for s in scores]
    # project_name is already in assessment_dict
    return jsonify(assessment_dict)


@api_bp.route('/v1/assessments/<int:assessment_id>/summary', methods=['GET'])
@token_required
def get_assessment_summary_route(assessment_id):
    """Get a summary of assessment results."""
    user_id = g.user_id
    
    conn = get_db()
    # Verify ownership
    assessment = conn.execute('''
        SELECT a.*, p.user_id 
        FROM assessments a
        JOIN projects p ON a.project_id = p.id
        WHERE a.id = ?
    ''', (assessment_id,)).fetchone()
    
    if not assessment or assessment['user_id'] != user_id:
        return jsonify({'error': 'Assessment not found'}), 404
    
    # Get assessment summary
    summary = get_assessment_summary(conn, assessment_id)
    
    return jsonify(summary)

@api_bp.route('/v1/assessments/<int:assessment_id>/responses', methods=['POST'])
@token_required
def get_assessment_responses(assessment_id):
    """Get a summary of assessment results."""
    user_id = g.user_id
    
    conn = get_db()
    # Verify ownership
    assessment = conn.execute('''
        SELECT a.*, p.user_id 
        FROM assessments a
        JOIN projects p ON a.project_id = p.id
        WHERE a.id = ?
    ''', (assessment_id,)).fetchone()
    
    if not assessment or assessment['user_id'] != user_id:
        return jsonify({'error': 'Assessment not found'}), 404
    
    # Get assessment summary
    summary = get_assessment_summary(conn, assessment_id)

@api_bp.route('/v1/sdg/goals', methods=['GET'])
def get_sdg_goals():
    """Get all SDG goals."""
    conn = get_db()
    goals = conn.execute('SELECT * FROM sdg_goals ORDER BY number').fetchall()
    
    # Convert row objects to dictionaries for JSON response
    goals_list = [dict(goal) for goal in goals]
    
    return jsonify(goals_list)

@api_bp.route('/v1/assessments/<int:assessment_id>/scores', methods=['POST'])
@token_required
def update_assessment_scores_api(assessment_id):
    user_id = g.user_id
    conn = get_db()
    # Verify ownership
    assessment = conn.execute('SELECT a.id FROM assessments a JOIN projects p ON a.project_id = p.id WHERE a.id = ? AND p.user_id = ?', (assessment_id, user_id)).fetchone()
    if not assessment:
        return jsonify({'error': 'Assessment not found or access denied'}), 404

    data = request.get_json()
    if not data or 'scores' not in data or not isinstance(data['scores'], list):
        return jsonify({'error': 'Invalid data format'}), 400

    try:
        print(f"[API DEBUG] Incoming scores data: {data}")
        for score_data in data['scores']:
            sdg_id = score_data.get('sdg_id')
            score = score_data.get('score')
            # Ensure score is a float (or int)
            try:
                score = float(score)
            except (TypeError, ValueError):
                print(f"[API DEBUG] Invalid score type for SDG {sdg_id}: {score}")
                continue
            notes = score_data.get('notes', '')
            if sdg_id is None or score is None:
                print(f"[API DEBUG] Skipping invalid score entry: {score_data}")
                continue
            try:
                print(f"[API DEBUG] About to INSERT OR REPLACE sdg_score for assessment_id={assessment_id}, sdg_id={sdg_id}, score={score}")
                conn.execute('''
                    INSERT OR REPLACE INTO sdg_scores
                    (assessment_id, sdg_id, score, notes, updated_at)
                    VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                ''', (assessment_id, sdg_id, score, notes))
                print(f"[API DEBUG] Successfully INSERT OR REPLACE sdg_score for assessment_id={assessment_id}, sdg_id={sdg_id}, score={score}")
            except Exception as db_err:
                print(f"DB Error for SDG {sdg_id}: {db_err}")
                return jsonify({'error': 'Database error during score update', 'details': str(db_err)}), 500
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM sdg_scores WHERE assessment_id = ?", (assessment_id,))
        count = cursor.fetchone()[0]
        print(f"[API DEBUG] Row count in sdg_scores for assessment {assessment_id} BEFORE commit: {count}")
        conn.commit()
        print(f"[API DEBUG] Commit successful for assessment {assessment_id}.")
        # Row count after commit
        cursor.execute("SELECT COUNT(*) FROM sdg_scores WHERE assessment_id = ?", (assessment_id,))
        count_after = cursor.fetchone()[0]
        print(f"[API DEBUG] Row count in sdg_scores for assessment {assessment_id} AFTER commit: {count_after}")
        # Immediately re-fetch all scores for this assessment for debug
        check_scores = conn.execute('SELECT * FROM sdg_scores WHERE assessment_id = ?', (assessment_id,)).fetchall()
        print(f"[API DEBUG] Scores found immediately after commit: {[dict(s) for s in check_scores]}")
        print("[API DEBUG] Scores committed successfully.")
        return jsonify({'success': True, 'assessment_id': assessment_id}), 200
    except Exception as e:
        conn.rollback()
        current_app.logger.error(f"Error updating scores via API: {e}")
        return jsonify({'error': 'Database error during score update', 'details': str(e)}), 500

@api_bp.route('/v1/dashboard', methods=['GET'])
@token_required
def get_dashboard_metrics_api():
    user_id = g.user_id
    conn = get_db()
    # Metrics
    project_count = conn.execute('SELECT COUNT(*) FROM projects WHERE user_id = ?', (user_id,)).fetchone()[0]
    assessment_count = conn.execute('SELECT COUNT(*) FROM assessments a JOIN projects p ON a.project_id = p.id WHERE p.user_id = ?', (user_id,)).fetchone()[0]
    avg_score_result = conn.execute('SELECT AVG(CAST(overall_score AS REAL)) FROM assessments a JOIN projects p ON a.project_id = p.id WHERE p.user_id = ? AND a.overall_score IS NOT NULL', (user_id,)).fetchone()
    avg_score = round(avg_score_result[0], 2) if avg_score_result and avg_score_result[0] is not None else None

    # Debug output
    print(f"[API DEBUG] Dashboard metrics: project_count={project_count}, assessment_count={assessment_count}, avg_score={avg_score}")

    return jsonify({
        'project_count': project_count,
        'assessment_count': assessment_count,
        'avg_score': avg_score,
        'sdg_performance': [],
        'recent_projects': []
    }), 200

@api_bp.route('/v1/sdg/relationships', methods=['GET'])
def get_sdg_relationships():
    """Get SDG relationships."""
    conn = get_db()
    relationships = conn.execute('''
        SELECT r.*, s.number as source_number, s.name as source_name,
               t.number as target_number, t.name as target_name
        FROM sdg_relationships r
        JOIN sdg_goals s ON r.source_sdg_id = s.id
        JOIN sdg_goals t ON r.target_sdg_id = t.id
        ORDER BY r.source_sdg_id, r.relationship_strength DESC
    ''').fetchall()
    
    # Convert row objects to dictionaries for JSON response
    relationships_list = [dict(rel) for rel in relationships]
    
    return jsonify(relationships_list)

@api_bp.route('/questionnaire/<int:assessment_id>/save', methods=['POST'])
@token_required
def save_questionnaire_response(assessment_id):
    """Save a questionnaire response."""
    user_id = g.user_id
    
    conn = get_db()
    # Verify ownership
    assessment = conn.execute('''
        SELECT a.*, p.user_id 
        FROM assessments a
        JOIN projects p ON a.project_id = p.id
        WHERE a.id = ?
    ''', (assessment_id,)).fetchone()
    
    if not assessment or assessment['user_id'] != user_id:
        return jsonify({'error': 'Assessment not found'}), 404
    
    try:
        data = request.json or {}
        question_id = data.get('question_id')
        response_value = data.get('response_value')
        
        if not question_id:
            return jsonify({'error': 'Missing question_id'}), 400
        
        # Get question info to calculate score
        question = conn.execute('''
            SELECT * FROM sdg_questions WHERE id = ?
        ''', (question_id,)).fetchone()
        
        if not question:
            return jsonify({'error': 'Question not found'}), 404
        
        # Calculate response score based on question type and response value
        from app.services.scoring_service import process_question_response
        response_score = process_question_response(
            question['question_type'],
            response_value,
            question.get('options'),
            question.get('max_score', 5)
        )
        
        # Check if response already exists
        existing = conn.execute('''
            SELECT id FROM question_responses 
            WHERE assessment_id = ? AND question_id = ?
        ''', (assessment_id, question_id)).fetchone()
        
        if existing:
            # Update existing response
            conn.execute('''
                UPDATE question_responses 
                SET response_value = ?, response_score = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (json.dumps(response_value) if isinstance(response_value, (list, dict)) else response_value,
                  response_score, existing['id']))
        else:
            # Create new response
            conn.execute('''
                INSERT INTO question_responses 
                (assessment_id, question_id, response_value, response_score, created_at, updated_at)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            ''', (assessment_id, question_id,
                  json.dumps(response_value) if isinstance(response_value, (list, dict)) else response_value,
                  response_score))
        
        # Update assessment timestamp
        conn.execute('''
            UPDATE assessments 
            SET updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (assessment_id,))
        
        conn.commit()
        
        return jsonify({
            'success': True,
            'question_id': question_id,
            'response_score': response_score
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/save-progress', methods=['POST'])
@token_required
def save_progress():
    """Save assessment progress for a section."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        # Validate required fields
        required_fields = ['project_id', 'section_id', 'section_data']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400

        project_id = data['project_id']
        section_id = data['section_id']
        section_data = data['section_data']

        # Verify project exists and user has access
        project = conn.execute('SELECT * FROM projects WHERE id = ?', (project_id,)).fetchone()
        if not project:
            return jsonify({'error': 'Project not found'}), 404
        if project['user_id'] != g.user_id:
            return jsonify({'error': 'Unauthorized access to project'}), 403

        # Get or create assessment progress
        progress = conn.execute('''
            SELECT * FROM assessment_progress WHERE project_id = ? AND user_id = ?
        ''', (project_id, g.user_id)).fetchone()

        if not progress:
            conn.execute('''
                INSERT INTO assessment_progress (project_id, user_id, data, last_updated)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ''', (project_id, g.user_id, {}, datetime.datetime.utcnow()))

        # Update section data
        if not progress['data']:
            progress['data'] = {}
        progress['data'][section_id] = section_data
        progress['last_updated'] = datetime.datetime.utcnow()

        conn.execute('''
            UPDATE assessment_progress SET data = ?, last_updated = ? WHERE project_id = ? AND user_id = ?
        ''', (json.dumps(progress['data']), progress['last_updated'], project_id, g.user_id))
        conn.commit()

        return jsonify({
            'status': 'success',
            'message': f'Progress saved for section {section_id}',
            'timestamp': progress['last_updated'].isoformat()
        })

    except Exception as e:
        conn.rollback()
        print(f"Error saving progress: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

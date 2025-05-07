"""
Project management routes.
Handles creating, viewing, editing, and deleting projects.
"""

from flask import Blueprint, render_template, redirect, url_for, request, flash, abort, jsonify, json, current_app
from flask_login import login_required, current_user
from app.models.project import Project
from app.models.assessment import Assessment, SdgScore
from app.models.sdg import SdgGoal
from app import db
from datetime import datetime
from ..scoring_logic import calculate_scores_python  # Import the scoring function
from app.utils.sdg_data import SDG_INFO  # Import SDG_INFO for the results page

projects_bp = Blueprint('projects', __name__)

@projects_bp.route('/', strict_slashes=False)
@login_required
def index():
    """Display all projects for the current user with search and sort functionality."""
    user_id = current_user.id
    
    # Get search and sort parameters from URL
    search_term = request.args.get('search', '').strip()
    sort_by = request.args.get('sort', 'name')  # Default sort by name
    
    # Start with base query
    query = Project.query.filter_by(user_id=user_id)
    
    # Apply search filter if present
    if search_term:
        query = query.filter(
            Project.name.ilike(f'%{search_term}%') |
            Project.description.ilike(f'%{search_term}%') |
            Project.location.ilike(f'%{search_term}%')
        )
    
    # Apply sorting
    if sort_by == 'name':
        query = query.order_by(Project.name.asc())
    elif sort_by == 'name_desc':
        query = query.order_by(Project.name.desc())
    elif sort_by == 'date_desc':
        query = query.order_by(Project.updated_at.desc())
    elif sort_by == 'date_asc':
        query = query.order_by(Project.updated_at.asc())
    elif sort_by == 'assessment_count_desc':
        # For assessment_count, we'll use a subquery
        assessment_count_subquery = db.session.query(
            Assessment.project_id,
            db.func.count(Assessment.id).label('assessment_count')
        ).group_by(Assessment.project_id).subquery()
        
        query = query.outerjoin(
            assessment_count_subquery,
            Project.id == assessment_count_subquery.c.project_id
        ).order_by(
            db.case(
                [(assessment_count_subquery.c.assessment_count == None, 0)],
                else_=assessment_count_subquery.c.assessment_count
            ).desc()
        )
    elif sort_by == 'assessment_count_asc':
        assessment_count_subquery = db.session.query(
            Assessment.project_id,
            db.func.count(Assessment.id).label('assessment_count')
        ).group_by(Assessment.project_id).subquery()
        
        query = query.outerjoin(
            assessment_count_subquery,
            Project.id == assessment_count_subquery.c.project_id
        ).order_by(
            db.case(
                [(assessment_count_subquery.c.assessment_count == None, 0)],
                else_=assessment_count_subquery.c.assessment_count
            ).asc()
        )
    else:
        query = query.order_by(Project.updated_at.desc())  # Default sort
    
    # Execute query and add assessment_count to each project
    projects = query.all()
    for project in projects:
        project.assessment_count = len(project.assessments)
    
    return render_template('projects/index.html', 
                         projects=projects, 
                         search_term=search_term, 
                         current_sort=sort_by)

@projects_bp.route('/<int:id>')
@login_required
def show(id):
    # --- Use get_or_404 ---
    project = Project.query.get_or_404(id)
    # --- END ---
    if project.user_id != current_user.id:
        abort(403)
    assessments = Assessment.query.filter_by(project_id=id).order_by(Assessment.created_at.desc()).all()
    return render_template('projects/show.html', project=project, assessments=assessments)


@projects_bp.route('/new', methods=['GET', 'POST'])
@login_required
def new_project():
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        project_type = request.form.get('project_type')
        location = request.form.get('location')
        size_sqm = request.form.get('size_sqm')
        
        if not name:
            flash('Project name is required.', 'danger')
            return render_template('projects/new.html')
        
        project = Project(
            name=name,
            description=description,
            project_type=project_type,
            location=location,
            size_sqm=float(size_sqm) if size_sqm else None,
            user_id=current_user.id
        )
        db.session.add(project)
        try:
            db.session.commit()
            flash('Project created successfully!', 'success')
            return redirect(url_for('projects.index'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating project: {str(e)}', 'danger')
            return render_template('projects/new.html')
    
    return render_template('projects/new.html')

@projects_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    """Edit an existing project."""
    project = Project.query.filter_by(id=id, user_id=current_user.id).first()
    if not project:
        flash('Project not found or you don\'t have permission to edit it', 'danger')
        return redirect(url_for('projects.index'))
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        project_type = request.form.get('project_type')
        location = request.form.get('location')
        size_sqm = request.form.get('size_sqm')
        try:
            project.name = name
            project.description = description
            project.project_type = project_type
            project.location = location
            project.size_sqm = float(size_sqm) if size_sqm else None
            db.session.commit()
            flash('Project updated successfully!', 'success')
            return redirect(url_for('projects.show', id=id))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating project: {str(e)}', 'danger')
    return render_template('projects/edit.html', project=project)

@projects_bp.route('/<int:id>/assessments/new', methods=['GET', 'POST'], strict_slashes=False)
@login_required
def new_assessment(id):
    """Create a new assessment for a project. Handles GET (show form) and POST (create or show errors)."""
    from app.models.assessment import Assessment
    project = Project.query.filter_by(id=id, user_id=current_user.id).first()
    if not project:
        flash('Project not found or you don\'t have permission to access it', 'danger')
        return redirect(url_for('projects.index'))

    if request.method == 'POST':
        # Example: validate a required field (e.g., 'assessment_name')
        assessment_name = request.form.get('assessment_name')
        if not assessment_name:
            flash('Assessment name is required.', 'danger')
            # Render a template for the assessment creation form with error
            return render_template('projects/new.html', project=project), 200
        # You can add more validation here as needed
        assessment = Assessment(project_id=id, user_id=current_user.id, status='draft', name=assessment_name)
        db.session.add(assessment)
        db.session.commit()
        assessment_id = assessment.id
        return redirect(url_for('assessments.questionnaire_step', project_id=id, assessment_id=assessment_id, step=1))

    # GET: show the form for creating an assessment
    return render_template('projects/new.html', project=project)

@projects_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    """Delete a project and all its associated data."""
    project = Project.query.filter_by(id=id, user_id=current_user.id).first()
    if not project:
        flash('Project not found or you don\'t have permission to delete it', 'danger')
        return redirect(url_for('projects.index'))
    try:
        # Optionally, delete related assessments and their data here if not handled by cascade
        # Example: Assessment.query.filter_by(project_id=id).delete()
        db.session.delete(project)
        db.session.commit()
        flash('Project deleted successfully', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting project: {str(e)}', 'danger')
    return redirect(url_for('projects.index'))

@projects_bp.route('/api/test', methods=['GET'])
def test_api():
    """Test API endpoint."""
    return jsonify({"message": "API is working"})

@projects_bp.route('/project/<int:project_id>/expert_assessment/save', methods=['POST'])
@login_required
def save_expert_assessment(project_id):
    """Save an expert assessment for a project."""
    project = Project.query.filter_by(id=project_id, user_id=current_user.id).first_or_404()

    if request.method == 'POST':
        assessment_data_json = request.form.get('assessment-data')

        if not assessment_data_json:
            flash('Error: Missing assessment data.', 'danger')
            return redirect(url_for('projects.view_project', project_id=project.id))

        try:
            # Parse the raw answers from the hidden input
            raw_expert_answers = json.loads(assessment_data_json)
        except json.JSONDecodeError:
            flash('Error: Invalid assessment data format.', 'danger')
            return redirect(url_for('projects.start_expert_assessment', project_id=project.id))

        # Create Assessment Record
        new_assessment = Assessment(
            project_id=project.id,
            user_id=current_user.id,
            status='completed',
            assessment_type='expert',
            raw_expert_data=raw_expert_answers,
            completed_at=datetime.utcnow()
        )
        db.session.add(new_assessment)

        # Calculate Scores using the imported function
        try:
            calculated_scores = calculate_scores_python(raw_expert_answers)
            if not isinstance(calculated_scores, list):
                raise ValueError("Scoring function did not return a list of scores")

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error calculating expert scores for project {project_id}: {e}")
            flash(f'Error calculating scores: {e}', 'danger')
            return redirect(url_for('projects.start_expert_assessment', project_id=project.id))

        # Create SdgScore Records
        total_sum = 0
        valid_scores_count = 0
        sdg_goals_map = {goal.number: goal.id for goal in SdgGoal.query.all()}

        for score_data in calculated_scores:
            sdg_number = score_data.get('number')
            sdg_goal_id = sdg_goals_map.get(sdg_number)

            if sdg_goal_id is None:
                current_app.logger.warning(f"Could not find SDG Goal ID for number {sdg_number}. Skipping score.")
                continue

            sdg_score_record = SdgScore(
                sdg_id=sdg_goal_id,
                total_score=score_data.get('total_score'),
                notes=raw_expert_answers.get(f'sdg{sdg_number}_notes', ''),  # Get notes from raw form data
                direct_score=score_data.get('direct_score'),  # Get these from the scoring function if available
                bonus_score=score_data.get('bonus_score')     # Get these from the scoring function if available
            )
            new_assessment.sdg_scores.append(sdg_score_record)

            # For calculating overall score
            if score_data.get('total_score') is not None:
                total_sum += score_data['total_score']
                valid_scores_count += 1

        # Calculate overall score
        new_assessment.overall_score = (total_sum / valid_scores_count) if valid_scores_count > 0 else 0

        # Final Save
        try:
            db.session.commit()
            flash('Expert Assessment saved successfully!', 'success')
            print(f"DEBUG: Redirecting to projects.show_expert_results with assessment_id={new_assessment.id}")
            return redirect(url_for('projects.show_expert_results', assessment_id=new_assessment.id))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error saving expert assessment to DB for project {project_id}: {e}")
            flash(f'Error saving assessment to database: {e}', 'danger')
            return redirect(url_for('projects.start_expert_assessment', project_id=project.id))

    return redirect(url_for('projects.view_project', project_id=project.id))

@projects_bp.route('/expert-assessment/<int:assessment_id>/results')
@login_required
def show_expert_results(assessment_id):
    """Display the results of an expert assessment."""
    # 1. Fetch the specific Assessment, ensuring it's an 'expert' type
    assessment = Assessment.query.filter_by(id=assessment_id, assessment_type='expert').first_or_404()
    project = assessment.project  # Access the related project via backref

    # Permission Check (User must own the project)
    if project.user_id != current_user.id:
        flash('You do not have permission to view this assessment.', 'danger')
        return redirect(url_for('projects.index'))

    # 2. Retrieve the calculated SDG scores with related SDG goal information
    sdg_scores_query = db.session.query(
        SdgScore.total_score,
        SdgScore.notes,
        SdgScore.direct_score,
        SdgScore.bonus_score,
        SdgGoal.number,
        SdgGoal.name,
        SdgGoal.color_code,
        SdgGoal.icon
    ).join(SdgGoal, SdgScore.sdg_id == SdgGoal.id)\
     .filter(SdgScore.assessment_id == assessment.id)\
     .order_by(SdgGoal.number)\
     .all()

    # Convert the query result into a list of dictionaries
    scores_data = []
    if sdg_scores_query:
        for score_row in sdg_scores_query:
            scores_data.append({
                'number': score_row.number,
                'name': score_row.name,
                'color_code': score_row.color_code or '#CCCCCC',  # Default color if none set
                'icon': score_row.icon,
                'total_score': round(score_row.total_score, 1) if score_row.total_score is not None else 0.0,
                'notes': score_row.notes or '',
                'direct_score': round(score_row.direct_score, 1) if score_row.direct_score is not None else None,
                'bonus_score': round(score_row.bonus_score, 1) if score_row.bonus_score is not None else None
            })
    else:
        flash('Could not retrieve SDG scores for this assessment.', 'warning')

    # 3. Render the results template with all necessary data
    return render_template('projects/expert_results.html',
                         assessment=assessment,
                         project=project,
                         scores_data=scores_data,
                         scores_json=json.dumps(scores_data),
                         SDG_INFO_json=json.dumps(SDG_INFO))  # Add SDG_INFO to the template context

@projects_bp.route('/project/<int:project_id>/expert-assessment')
@login_required
def expert_assessment(project_id):
    """Start a new expert assessment for a project."""
    project = Project.query.filter_by(id=project_id, user_id=current_user.id).first_or_404()
    return render_template('questionnaire/expert_assessment.html', project=project)

"""
Project management routes.
Handles creating, viewing, editing, and deleting projects.
"""

from flask import Blueprint, render_template, redirect, url_for, request, flash, abort, jsonify
from flask_login import login_required, current_user
from app.models.project import Project
from app.models.assessment import Assessment
from app import db

projects_bp = Blueprint('projects', __name__)

@projects_bp.route('/', strict_slashes=False)
@login_required
def index():
    """Display all projects for the current user."""
    user_id = current_user.id
    # Get all projects for the user, newest first
    projects = Project.query.filter_by(user_id=user_id).order_by(Project.updated_at.desc()).all()
    # Add assessment_count attribute to each project
    for project in projects:
        project.assessment_count = len(project.assessments)
    return render_template('projects/index.html', projects=projects)

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
            return render_template('assessments/new.html', project=project), 200
        # You can add more validation here as needed
        assessment = Assessment(project_id=id, user_id=current_user.id, status='draft', name=assessment_name)
        db.session.add(assessment)
        db.session.commit()
        assessment_id = assessment.id
        return redirect(url_for('assessments.questionnaire_step', project_id=id, assessment_id=assessment_id, step=1))

    # GET: show the form for creating an assessment
    return render_template('assessments/new.html', project=project)

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

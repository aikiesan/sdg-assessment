"""
Project management routes.
Handles creating, viewing, editing, and deleting projects.
"""

from flask import Blueprint, render_template, redirect, url_for, request, flash, abort, jsonify
from flask_login import login_required, current_user
from app.models.project import Project
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

@projects_bp.route('/<int:id>', methods=['GET'], strict_slashes=False)
@login_required
def show(id):
    """Show project details."""
    user_id = current_user.id
    project = Project.query.filter_by(id=id, user_id=user_id).first()
    if not project:
        flash('Project not found or permission denied', 'danger')
        return redirect(url_for('projects.index'))
    # Keep assessments raw SQL for now
    from app.utils.db import get_db
    conn = get_db()
    assessments = conn.execute('SELECT * FROM assessments WHERE project_id = ? ORDER BY created_at DESC', (id,)).fetchall()
    assessments_list = [dict(a) for a in assessments]
    return render_template('projects/show.html', project=project, assessments=assessments_list)

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

@projects_bp.route('/<int:id>/assessments/new', strict_slashes=False)
@login_required
def new_assessment(id):
    """Create a new assessment for a project."""
    from app.models.assessment import Assessment
    project = Project.query.filter_by(id=id, user_id=current_user.id).first()
    if not project:
        flash('Project not found or you don\'t have permission to access it', 'danger')
        return redirect(url_for('projects.index'))
    # Create or find a draft assessment for this project and user
    assessment = Assessment.query.filter_by(project_id=id, user_id=current_user.id, status='draft').first()
    if not assessment:
        assessment = Assessment(project_id=id, user_id=current_user.id, status='draft')
        db.session.add(assessment)
        db.session.commit()
        assessment_id = assessment.id
    else:
        assessment_id = assessment.id
    return redirect(url_for('assessments.questionnaire_step', project_id=id, assessment_id=assessment_id, step=1))

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
        flash('Project and all related assessments have been deleted', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting project: {str(e)}', 'danger')
    return redirect(url_for('projects.index'))

@projects_bp.route('/api/test', methods=['GET'])
def test_api():
    """Test API endpoint."""
    return jsonify({"message": "API is working"})

"""
Project model.
Represents architectural projects in the application.
"""

from app import db
from datetime import datetime

class Project(db.Model):
    __tablename__ = 'projects'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    project_type = db.Column(db.String(100))
    location = db.Column(db.String(255))
    size_sqm = db.Column(db.Float)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = db.relationship('User', back_populates='projects')
    assessments = db.relationship('Assessment', back_populates='project', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Project {self.name}>'

# Old raw SQL methods removed for ORM migration.

        projects = []
        for project_data in projects_data:
            project = Project(
                id=project_data['id'],
                name=project_data['name'],
                description=project_data['description'],
                project_type=project_data['project_type'],
                location=project_data['location'],
                size_sqm=project_data['size_sqm'],
                user_id=project_data['user_id'],
                created_at=project_data['created_at'],
                updated_at=project_data['updated_at']
            )
            # Add assessment count as an attribute
            project.assessment_count = project_data['assessment_count']
            projects.append(project)
        return projects

    def save(self):
        """Save the project to the database (create or update)."""
        conn = get_db()
        if self.id:
            # Update existing project
            conn.execute('''
                UPDATE projects
                SET name = ?, description = ?, project_type = ?, location = ?, size_sqm = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ? AND user_id = ?
            ''', (self.name, self.description, self.project_type, self.location, self.size_sqm, self.id, self.user_id))
        else:
            # Create new project
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO projects (name, description, project_type, location, size_sqm, user_id, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            ''', (self.name, self.description, self.project_type, self.location, self.size_sqm, self.user_id))
            self.id = cursor.lastrowid
        conn.commit()
        return self

    def delete(self):
        """Delete the project and all its assessments."""
        conn = get_db()
        # Delete all related assessment data first
        conn.execute('DELETE FROM sdg_actions WHERE assessment_id IN (SELECT id FROM assessments WHERE project_id = ?)', (self.id,))
        conn.execute('DELETE FROM sdg_scores WHERE assessment_id IN (SELECT id FROM assessments WHERE project_id = ?)', (self.id,))
        conn.execute('DELETE FROM question_responses WHERE assessment_id IN (SELECT id FROM assessments WHERE project_id = ?)', (self.id,))
        conn.execute('DELETE FROM assessments WHERE project_id = ?', (self.id,))
        # Then delete the project
        conn.execute('DELETE FROM projects WHERE id = ?', (self.id,))
        conn.commit()

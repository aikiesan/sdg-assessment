"""
This module defines the Project model, representing architectural projects
within the application. It includes attributes for project details,
relationships to users and assessments, and validation logic.
"""

from app import db
from datetime import datetime
from sqlalchemy.orm import validates

class Project(db.Model):
    """
    Represents an architectural project in the application.

    Attributes:
        id (int): Primary key for the project.
        name (str): Name of the project (max 255 characters, required).
        description (str): Detailed description of the project.
        project_type (str): Type of project (e.g., residential, commercial).
        location (str): Physical location or address of the project.
        size_sqm (float): Size of the project in square meters.
        user_id (int): Foreign key linking to the 'user' table, indicating the owner/creator.
        created_at (datetime): Timestamp of when the project was created.
        updated_at (datetime): Timestamp of the last update to the project.
        start_date (datetime): Proposed or actual start date of the project.
        end_date (datetime): Proposed or actual end date of the project.
        budget (float): Estimated or actual budget for the project.
        sector (str): Sector the project belongs to (e.g., Healthcare, Education).
        status (str): Current status of the project (e.g., planning, in_progress, completed).
        user (relationship): SQLAlchemy relationship to the 'User' model.
        assessments (relationship): SQLAlchemy relationship to the 'Assessment' model.
    """
    __tablename__ = 'projects'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False) # Name of the project, cannot be null
    description = db.Column(db.Text) # Detailed description of the project
    project_type = db.Column(db.String(100)) # E.g., 'Residential', 'Commercial', 'Renovation'
    location = db.Column(db.String(255)) # Physical address or general location
    size_sqm = db.Column(db.Float) # Size of the project in square meters
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False) # Foreign key to User table
    created_at = db.Column(db.DateTime, default=datetime.utcnow) # Timestamp of creation
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow) # Timestamp of last update
    start_date = db.Column(db.DateTime) # Planned or actual start date of the project
    end_date = db.Column(db.DateTime) # Planned or actual end date of the project
    budget = db.Column(db.Float) # Estimated or actual budget for the project
    sector = db.Column(db.String(100)) # Industry sector, e.g., 'Healthcare', 'Education', 'Public'
    status = db.Column(db.String(50), nullable=True, default='planning') # Current stage of the project, e.g., 'planning', 'construction'

    user = db.relationship('User', back_populates='projects')
    assessments = db.relationship('Assessment', back_populates='project', cascade='all, delete-orphan')

    @validates('size_sqm')
    def validate_size_sqm(self, key, value):
        """
        Validates the 'size_sqm' attribute.
        Ensures that the size is a positive number and not excessively large.
        """
        if value is not None:
            if not isinstance(value, (int, float)):
                raise ValueError("Size must be a number.")
            if value <= 0:
                raise ValueError("Size must be a positive number.")
            if value > 1000000: # Example upper limit
                raise ValueError("Size must be less than 1,000,000 sq meters.")
        return value
    
    @validates('budget')
    def validate_budget(self, key, value):
        """
        Validates the 'budget' attribute.
        Ensures that the budget is a positive number.
        """
        if value is not None:
            if not isinstance(value, (int, float)):
                raise ValueError("Budget must be a number.")
            if value <= 0:
                raise ValueError("Budget must be a positive number.")
        return value
    
    @validates('end_date')
    def validate_end_date(self, key, value):
        """
        Validates the 'end_date' attribute.
        Ensures that the end date is not before the start date.
        """
        if value is not None and self.start_date is not None:
            if value < self.start_date:
                raise ValueError("End date must be after start date.")
        return value
    
    @validates('name')
    def validate_name(self, key, value):
        """
        Validates the 'name' attribute.
        Ensures that the project name is provided and within length limits.
        """
        if not value:
            raise ValueError("Project name is required.")
        if len(value) > 100: # Max length for project name
            raise ValueError("Project name must be less than 100 characters.")
        return value
    
    @validates('description')
    def validate_description(self, key, value):
        """
        Validates the 'description' attribute.
        Ensures that the description is within length limits.
        """
        if value and len(value) > 500: # Max length for description
            raise ValueError("Description must be less than 500 characters.")
        return value
    
    @validates('location')
    def validate_location(self, key, value):
        """
        Validates the 'location' attribute.
        Ensures that the location string is within length limits.
        """
        if value and len(value) > 255: # Max length for location
            raise ValueError("Location must be less than 255 characters.")
        return value
    
    @validates('sector')
    def validate_sector(self, key, value):
        """
        Validates the 'sector' attribute.
        Checks if the sector is one of the predefined valid sectors.
        Attempts to correct case if a valid sector is entered with different casing.
        """
        valid_sectors = [
            'Residential', 'Commercial', 'Education', 'Healthcare', 
            'Transportation', 'Technology', 'Energy', 'Industrial',
            'Agriculture', 'Entertainment', 'Hospitality', 'Public', 'Other'
        ]
        # Standardize input for comparison
        if value and value.lower() not in [s.lower() for s in valid_sectors]:
            # If the title-cased version is a valid sector, use that. Otherwise, keep original (it might be 'Other' or a new one)
            return value.title() if value.title() in valid_sectors else value
        elif value: # If it is in the list (case-insensitive), ensure it's stored in a standard format (Title Case)
            for s_valid in valid_sectors:
                if s_valid.lower() == value.lower():
                    return s_valid
        return value # Return original value if it's None or already valid/corrected

    def __repr__(self):
        """
        Returns a string representation of the Project object.
        """
        return f'<Project {self.name}>'

# Old raw SQL methods were previously here.
# They have been removed as part of the migration to SQLAlchemy ORM.
# For example, methods like get_all_for_user, get_by_id were here.

# The following section contains commented-out code that appears to be part of
# a previous raw SQL implementation for fetching projects.
# This is preserved for reference but is not active.
# """
#        projects = []
#        for project_data in projects_data:
#            project = Project(
#                id=project_data['id'],
#                name=project_data['name'],
#                description=project_data['description'],
#                project_type=project_data['project_type'],
#                location=project_data['location'],
#                size_sqm=project_data['size_sqm'],
#                user_id=project_data['user_id'],
#                created_at=project_data['created_at'],
#                updated_at=project_data['updated_at'],
#                start_date=project_data.get('start_date'),
#                end_date=project_data.get('end_date'),
#                budget=project_data.get('budget'),
#                sector=project_data.get('sector')
#            )
#            # Add assessment count as an attribute
#            project.assessment_count = project_data['assessment_count']
#            projects.append(project)
#        return projects
# """

    def save(self):
        """
        Save the project to the database (create or update).
        This method currently uses raw SQL.
        """
        # TODO: Refactor this raw SQL logic to use SQLAlchemy session operations (db.session.add(), db.session.commit()).
        conn = get_db() # Assumes get_db() provides a database connection.
        if self.id:
            # Update existing project
            conn.execute('''
                UPDATE projects
                SET name = ?, description = ?, project_type = ?, location = ?, size_sqm = ?, 
                    start_date = ?, end_date = ?, budget = ?, sector = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ? AND user_id = ?
            ''', (self.name, self.description, self.project_type, self.location, self.size_sqm,
                  self.start_date, self.end_date, self.budget, self.sector, self.id, self.user_id))
        else:
            # Create new project
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO projects (name, description, project_type, location, size_sqm, user_id, 
                                    start_date, end_date, budget, sector, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            ''', (self.name, self.description, self.project_type, self.location, self.size_sqm, self.user_id,
                  self.start_date, self.end_date, self.budget, self.sector))
            self.id = cursor.lastrowid
        conn.commit()
        return self

    def delete(self):
        """
        Delete the project and all its assessments.
        This method currently uses raw SQL.
        """
        # TODO: Refactor this raw SQL logic to use SQLAlchemy cascade options or explicit session.delete() calls.
        conn = get_db() # Assumes get_db() provides a database connection.
        # Delete all related assessment data first
        # These should ideally be handled by cascade deletes in the database or via SQLAlchemy relationships.
        conn.execute('DELETE FROM sdg_actions WHERE assessment_id IN (SELECT id FROM assessments WHERE project_id = ?)', (self.id,))
        conn.execute('DELETE FROM sdg_scores WHERE assessment_id IN (SELECT id FROM assessments WHERE project_id = ?)', (self.id,))
        conn.execute('DELETE FROM question_responses WHERE assessment_id IN (SELECT id FROM assessments WHERE project_id = ?)', (self.id,))
        conn.execute('DELETE FROM assessments WHERE project_id = ?', (self.id,)) # This is handled by cascade='all, delete-orphan' on assessments relationship
        # Then delete the project
        conn.execute('DELETE FROM projects WHERE id = ?', (self.id,))
        conn.commit()

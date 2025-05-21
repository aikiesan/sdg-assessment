"""
Project Service Module.

This module provides the business logic for project management.
It primarily uses raw SQL queries executed via a direct database connection
obtained through `app.utils.db.get_db()`.
Functions handle creating, retrieving, updating, and deleting projects,
along with listing projects with pagination and filtering.

TODO: This module should be evaluated for migration to SQLAlchemy ORM
to improve database abstraction, type safety, code readability, and maintainability.
"""
from flask import abort
from app.utils.db import get_db # Utility to get a database connection
import logging

logger = logging.getLogger(__name__)

def get_projects(user_id, page=1, per_page=10, filters=None):
    """
    Retrieves a paginated list of projects for a specific user, with optional filtering.
    Uses raw SQL for database interaction.

    Args:
        user_id (int): The ID of the user whose projects are to be retrieved.
        page (int): The page number for pagination (default is 1).
        per_page (int): The number of projects per page (default is 10).
        filters (dict, optional): A dictionary of filters to apply.
            Supported filters:
            - 'project_type' (str): Filter by project type.
            - 'status' (str): Filter by project status.
            - 'search' (str): Search term for project name or description (case-insensitive).

    Returns:
        list[dict]: A list of dictionaries, where each dictionary represents a project.
    """
    # TODO: Consider refactoring this function to use SQLAlchemy ORM for better database abstraction, type safety, and maintainability.
    conn = get_db() # Obtain a database connection.
    
    # Base SQL query to select projects for the user.
    sql = "SELECT * FROM projects WHERE user_id = ?"
    params = [user_id]

    # Apply filters if provided.
    if filters:
        if 'project_type' in filters and filters['project_type']:
            sql += " AND project_type = ?"
            params.append(filters['project_type'])
        if 'status' in filters and filters['status']:
            sql += " AND status = ?"
            params.append(filters['status'])
        if 'search' in filters and filters['search']:
            # Add conditions for searching in name or description.
            sql += " AND (name LIKE ? OR description LIKE ?)"
            search_term = f"%{filters['search']}%" # Prepare search term for LIKE operator.
            params.extend([search_term, search_term])
    
    # Add ordering, limit, and offset for pagination.
    sql += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
    params.extend([per_page, (page - 1) * per_page])
    
    # Execute the dynamically constructed SQL query.
    projects_data = conn.execute(sql, tuple(params)).fetchall()
    
    # The comment "conn.close() removed; teardown handles DB connection." indicates that
    # the database connection is managed by a Flask teardown context,
    # ensuring it's closed automatically after the request.
    return [dict(row) for row in projects_data] # Convert SQL rows to dictionaries.

def get_project(project_id, user_id=None):
    """
    Retrieves a single project by its ID.
    Optionally checks if the user_id matches the project's user_id for authorization.
    Uses raw SQL for database interaction.

    Args:
        project_id (int): The ID of the project to retrieve.
        user_id (int, optional): The ID of the user making the request.
                                 If provided, ownership is checked.

    Returns:
        dict: A dictionary representing the project if found and authorized.

    Raises:
        werkzeug.exceptions.NotFound: If the project with project_id is not found.
        werkzeug.exceptions.Forbidden: If user_id is provided and does not match the project's owner.
    """
    # TODO: Consider refactoring this function to use SQLAlchemy ORM for better database abstraction, type safety, and maintainability.
    conn = get_db() # Obtain a database connection.
    
    # SQL query to fetch a project by its ID.
    project_data = conn.execute('SELECT * FROM projects WHERE id = ?', (project_id,)).fetchone()
    
    if not project_data:
        # Project not found, abort with a 404 error.
        # The comment "conn.close() removed; teardown handles DB connection." applies here as well.
        abort(404, description=f"Project with ID {project_id} not found.")
    
    # Authorization check: if user_id is provided, ensure it matches the project's user_id.
    if user_id is not None and project_data['user_id'] != user_id:
        # Log unauthorized access attempt.
        logger.warning(f"User {user_id} attempted to access project {project_id} owned by {project_data['user_id']}.")
        # Abort with a 403 Forbidden error.
        # The comment "conn.close() removed; teardown handles DB connection." applies here as well.
        abort(403, description="You do not have permission to access this project.")
        
    result = dict(project_data) # Convert SQL row to dictionary.
    # The comment "conn.close() removed; teardown handles DB connection." applies here as well.
    return result

def create_project(data, user_id):
    """
    Creates a new project with the given data for the specified user.
    Uses raw SQL for database interaction.

    Args:
        data (dict): A dictionary containing project attributes (e.g., 'name', 'description').
                     Required keys: 'name'.
                     Optional keys: 'description', 'project_type', 'location', 'size_sqm'.
        user_id (int): The ID of the user creating the project.

    Returns:
        dict: A dictionary representing the newly created project.

    Raises:
        Exception: If an error occurs during database insertion (e.g., SQL error).
                   The transaction is rolled back.
    """
    # TODO: Consider refactoring this function to use SQLAlchemy ORM for better database abstraction, type safety, and maintainability.
    conn = get_db() # Obtain a database connection.
    try:
        # SQL query to insert a new project.
        # Uses parameterized query to prevent SQL injection.
        conn.execute(
            'INSERT INTO projects (name, description, project_type, location, size_sqm, user_id) VALUES (?, ?, ?, ?, ?, ?)',
            (
                data['name'], # Project name is required.
                data.get('description', ''), # Optional description, defaults to empty string.
                data.get('project_type'),    # Optional project_type.
                data.get('location'),        # Optional location.
                data.get('size_sqm'),        # Optional size_sqm.
                user_id
            )
        )
        conn.commit() # Commit the transaction to save the new project.
        
        # Retrieve the newly created project using last_insert_rowid() (SQLite specific).
        # For other databases, a different approach might be needed (e.g., RETURNING id).
        project_data = conn.execute('SELECT * FROM projects WHERE rowid = last_insert_rowid()').fetchone()
        
        # Log project creation.
        logger.info(f"Project {project_data['id']} created by user {user_id}")
        result = dict(project_data)
        # The comment "conn.close() removed; teardown handles DB connection." applies here as well.
        return result
    except Exception as e:
        conn.rollback() # Rollback transaction on error.
        # Log the error.
        logger.error(f"Error creating project for user {user_id}: {str(e)}. Data: {data}")
        # The comment "conn.close() removed; teardown handles DB connection." applies here as well.
        raise # Re-raise the exception to be handled by higher-level error handlers.

def update_project(project_id, data, user_id):
    """
    Updates an existing project identified by project_id.
    Ensures that the user making the request owns the project.
    Uses raw SQL for database interaction; dynamically constructs the SET clause.

    Args:
        project_id (int): The ID of the project to update.
        data (dict): A dictionary containing the project attributes to update.
                     Supported keys: 'name', 'description', 'project_type', 'location', 'size_sqm', 'status'.
        user_id (int): The ID of the user making the update request.

    Returns:
        dict: A dictionary representing the updated project.

    Raises:
        werkzeug.exceptions.Forbidden: If the user does not own the project or if the project doesn't exist.
        Exception: If an error occurs during the database update.
                   The transaction is rolled back.
    """
    # TODO: Consider refactoring this function to use SQLAlchemy ORM for better database abstraction, type safety, and maintainability.
    conn = get_db() # Obtain a database connection.
    
    # First, verify ownership and existence of the project.
    # SQL query to fetch the project by ID.
    project = conn.execute('SELECT * FROM projects WHERE id = ?', (project_id,)).fetchone()
    
    if not project or project['user_id'] != user_id:
        # Log unauthorized attempt or attempt to update non-existent project.
        logger.warning(f"User {user_id} failed to update project {project_id}. Project not found or permission denied.")
        # Abort with a 403 Forbidden error (could also be 404 if project doesn't exist, but 403 covers both here).
        # The comment "conn.close() removed; teardown handles DB connection." applies here as well.
        abort(403, description="Project not found or you do not have permission to update it.")
        
    try:
        fields_to_update = []
        params_for_update = []
        
        # Dynamically build the SET part of the SQL query based on data provided.
        # This ensures only provided fields are updated.
        if 'name' in data:
            fields_to_update.append('name = ?')
            params_for_update.append(data['name'])
        if 'description' in data:
            fields_to_update.append('description = ?')
            params_for_update.append(data['description'])
        if 'project_type' in data:
            fields_to_update.append('project_type = ?')
            params_for_update.append(data['project_type'])
        if 'location' in data:
            fields_to_update.append('location = ?')
            params_for_update.append(data['location'])
        if 'size_sqm' in data:
            fields_to_update.append('size_sqm = ?')
            params_for_update.append(data['size_sqm'])
        if 'status' in data: # Added status to the list of updatable fields
            fields_to_update.append('status = ?')
            params_for_update.append(data['status'])
            
        if not fields_to_update:
            # No fields to update, return the project as is.
            # The comment "conn.close() removed; teardown handles DB connection." applies here as well.
            return dict(project) 
            
        params_for_update.append(project_id) # Add project_id for the WHERE clause.
        
        # Construct and execute the UPDATE SQL query.
        # Uses parameterized query to prevent SQL injection.
        # The f-string is used to build the SET part of the query with field names,
        # which is generally safe as field names are controlled by the application, not user input.
        update_sql = f"UPDATE projects SET {', '.join(fields_to_update)} WHERE id = ?"
        conn.execute(update_sql, tuple(params_for_update))
        conn.commit() # Commit the transaction.
        
        # Log project update.
        logger.info(f"Project {project_id} updated by user {user_id}. Data: {data}")
        
        # Fetch the updated project data.
        updated_project_data = conn.execute('SELECT * FROM projects WHERE id = ?', (project_id,)).fetchone()
        result = dict(updated_project_data)
        # The comment "conn.close() removed; teardown handles DB connection." applies here as well.
        return result
    except Exception as e:
        conn.rollback() # Rollback transaction on error.
        # Log the error.
        logger.error(f"Error updating project {project_id} for user {user_id}: {str(e)}. Data: {data}")
        # The comment "conn.close() removed; teardown handles DB connection." applies here as well.
        raise # Re-raise the exception.

def delete_project(project_id, user_id):
    """
    Deletes a project identified by project_id.
    Ensures that the user making the request owns the project.
    Uses raw SQL for database interaction.

    Args:
        project_id (int): The ID of the project to delete.
        user_id (int): The ID of the user making the delete request.

    Returns:
        bool: True if the deletion was successful.

    Raises:
        werkzeug.exceptions.Forbidden: If the user does not own the project or if the project doesn't exist.
        Exception: If an error occurs during database deletion.
                   The transaction is rolled back.
    """
    # TODO: Consider refactoring this function to use SQLAlchemy ORM for better database abstraction, type safety, and maintainability.
    conn = get_db() # Obtain a database connection.
    
    # First, verify ownership and existence of the project.
    # SQL query to fetch the project by ID.
    project = conn.execute('SELECT * FROM projects WHERE id = ?', (project_id,)).fetchone()
    
    if not project or project['user_id'] != user_id:
        # Log unauthorized attempt or attempt to delete non-existent project.
        logger.warning(f"User {user_id} failed to delete project {project_id}. Project not found or permission denied.")
        # Abort with a 403 Forbidden error.
        # The comment "conn.close() removed; teardown handles DB connection." applies here as well.
        abort(403, description="Project not found or you do not have permission to delete it.")
        
    try:
        # SQL query to delete the project by its ID.
        # Uses parameterized query.
        conn.execute('DELETE FROM projects WHERE id = ?', (project_id,))
        conn.commit() # Commit the transaction.
        
        # Log project deletion.
        logger.info(f"Project {project_id} deleted by user {user_id}")
        # The comment "conn.close() removed; teardown handles DB connection." applies here as well.
        return True
    except Exception as e:
        conn.rollback() # Rollback transaction on error.
        # Log the error.
        logger.error(f"Error deleting project {project_id} for user {user_id}: {str(e)}")
        # The comment "conn.close() removed; teardown handles DB connection." applies here as well.
        raise # Re-raise the exception.
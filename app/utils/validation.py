"""
Validation Utilities.

This module provides a collection of functions for input validation and sanitization.
These functions are used throughout the application to ensure data integrity,
security (by mitigating risks like XSS), and adherence to specific formats
for various data types such as emails, passwords, project details, assessment
responses, SDG data, and question data.
"""

import re  # Used for regular expression operations, primarily for pattern matching in strings.
import json # Used for parsing JSON strings, particularly for checklist options.
from flask import request # Used to access incoming request data, specifically form data.

def sanitize_input(value):
    """
    Sanitizes user input by removing potentially dangerous characters and cleaning the string.

    This function aims to mitigate cross-site scripting (XSS) vulnerabilities and
    other injection attacks by stripping out script tags, HTML tags, and control characters.
    It also normalizes whitespace for consistency.

    Args:
        value (any): The input value to be sanitized. It will be converted to a string.

    Returns:
        str or None: The sanitized string, or None if the input value was None.
    """
    if value is None:
        return None # Return None if input is None, avoiding errors with str() conversion.
    
    # Ensure the value is a string for regex operations.
    value_str = str(value)
    
    # Step 1: Remove any <script>...</script> tags and their content.
    # re.DOTALL makes '.' match newlines as well, for multi-line scripts.
    sanitized_value = re.sub(r'<script.*?>.*?</script>', '', value_str, flags=re.DOTALL | re.IGNORECASE)
    
    # Step 2: Replace any other HTML tags (e.g., <div>, <p>, <img>) with a single space.
    # This helps to remove markup while preserving some spacing.
    sanitized_value = re.sub(r'<[^>]*>', ' ', sanitized_value)
    
    # Step 3: Remove control characters (ASCII 0-31 and 127).
    # These characters are often not displayable and can be used in some attacks.
    sanitized_value = re.sub(r'[\x00-\x1F\x7F]', '', sanitized_value)
    
    # Step 4: Normalize whitespace by replacing multiple consecutive spaces with a single space.
    sanitized_value = re.sub(r'\s+', ' ', sanitized_value)
    
    # Step 5: Trim leading and trailing whitespace from the string.
    sanitized_value = sanitized_value.strip()
    
    return sanitized_value

def validate_email(email):
    """
    Validates the format of an email address using a basic regular expression.

    Args:
        email (str): The email address string to validate.

    Returns:
        bool: True if the email format is considered valid, False otherwise.
    """
    if not email:
        return False # An empty string or None is not a valid email.
    
    # A commonly used regex for basic email validation.
    # It checks for a pattern like 'username@domain.extension'.
    # This is not foolproof (RFC 5322 is complex) but covers most common cases.
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email)) # Returns True if the pattern matches, False otherwise.

def validate_password(password):
    """
    Validates password strength based on predefined criteria.

    Checks for:
    - Minimum length (at least 8 characters).
    - Presence of at least one digit.
    - Presence of at least one uppercase letter.
    - Presence of at least one lowercase letter.

    Args:
        password (str): The password string to validate.

    Returns:
        tuple[bool, str]: A tuple containing:
                          - bool: True if the password meets all criteria, False otherwise.
                          - str: An error message if validation fails, or an empty string if valid.
    """
    # Check 1: Minimum length.
    if not password or len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    # Check 2: At least one digit.
    if not re.search(r'\d', password):
        return False, "Password must contain at least one digit"
    
    # Check 3: At least one uppercase letter.
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    
    # Check 4: At least one lowercase letter.
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    
    # If all checks pass:
    return True, ""

def validate_project_data(data):
    """
    Validates project data provided in a dictionary (e.g., from a form).

    Checks for required fields and adherence to length or value constraints.

    Args:
        data (dict): A dictionary containing project attributes.
                     Expected keys: 'name', 'description', 'size_sqm'.

    Returns:
        list[str]: A list of error messages. The list is empty if all validations pass.
    """
    errors = [] # Initialize an empty list to store error messages.
    
    # Check 1: Project name is required.
    if not data.get('name'):
        errors.append('Project name is required')
    
    # Check 2: Project name length.
    if data.get('name') and len(data['name']) > 100:
        errors.append('Project name must be less than 100 characters')
    
    # Check 3: Project description length.
    if data.get('description') and len(data['description']) > 500:
        errors.append('Description must be less than 500 characters')
    
    # Check 4: Project size (size_sqm) validation.
    if data.get('size_sqm'):
        try:
            size = float(data['size_sqm']) # Attempt to convert to float.
            # Ensure size is positive and within a reasonable upper limit (e.g., 1 million sq meters).
            if size <= 0 or size > 1000000:  
                errors.append('Size must be a positive number less than 1,000,000 sq meters')
        except ValueError:
            errors.append('Size must be a valid number') # Error if conversion to float fails.
    
    return errors

def validate_assessment_response(question_type, value, options=None):
    """
    Validates a response to an assessment question based on its type.

    Args:
        question_type (str): The type of the question (e.g., 'select', 'checklist').
        value (any): The response value provided by the user.
        options (list, optional): A list of valid options, typically for 'checklist'
                                  questions, to validate against. Each option can be a
                                  string or a dict with 'key' or 'text'.

    Returns:
        tuple[bool, str]: A tuple containing:
                          - bool: True if the response is valid for the question type, False otherwise.
                          - str: An error message if validation fails, or an empty string if valid.
    """
    # Validation for 'select' (e.g., radio button) type questions.
    if question_type == 'select':
        # Expected value is a score, typically an integer between 0 and 5.
        try:
            score = int(value)
            if not (0 <= score <= 5): # Check if score is within the valid range.
                return False, "Score must be between 0 and 5"
        except (ValueError, TypeError): # Handle cases where value is not a valid integer.
            return False, "Score must be a number"
    
    # Validation for 'checklist' (e.g., checkbox group) type questions.
    elif question_type == 'checklist':
        try:
            # The value might be a JSON string representing a list of selected option keys, or already a list.
            selected_options = json.loads(value) if isinstance(value, str) else value
            if not isinstance(selected_options, list):
                return False, "Selected options must be a list"
            
            # If `options` (the master list of valid options for the question) are provided,
            # validate that each selected item is actually a valid option.
            if options:
                valid_keys = []
                for opt in options: # Build a list of valid keys/texts from the master options.
                    if isinstance(opt, dict):
                        # Option might be a dict like {'key': 'option_a', 'text': 'Option A'} or just {'text': 'Option A'}
                        valid_keys.append(opt.get('key', opt.get('text'))) 
                    elif isinstance(opt, str):
                        valid_keys.append(opt) # Option might be a simple string.
                
                # Check each selected option against the list of valid keys.
                for selection in selected_options:
                    if selection not in valid_keys:
                        return False, f"Invalid selection: {selection}"
        except json.JSONDecodeError: # Handle error if `value` is a string but not valid JSON.
            return False, "Invalid JSON format for selected options"
    
    # For other question types, or if no specific validation rule is matched, assume valid.
    # Add more `elif` blocks here for other question types as needed.
    
    return True, "" # If all checks pass for the given type, or if type has no validation.

def validate_request_form():
    """
    Validates and sanitizes all form fields in the current Flask request.

    This function iterates through all items in `request.form` (POST data)
    and applies the `sanitize_input` function to each value.

    Returns:
        dict: A dictionary containing the sanitized form data, where keys are
              the original form field names and values are their sanitized versions.
              Returns an empty dictionary if the request method is not 'POST'.
    """
    if request.method != 'POST':
        # Only process POST requests, as form data is typically sent via POST.
        return {} 
    
    sanitized_data = {}
    for key, value in request.form.items():
        # Apply sanitization to each form value.
        sanitized_data[key] = sanitize_input(value)
    
    return sanitized_data

def validate_sdg_data(data):
    """
    Validates Sustainable Development Goal (SDG) form data.

    Checks for required fields (name, number) and specific format constraints
    (number range, color code format).

    Args:
        data (dict): A dictionary containing SDG attributes.
                     Expected keys: 'name', 'number', 'color_code'.

    Returns:
        list[str]: A list of error messages. Empty if all validations pass.
    """
    errors = []
    
    # Check 1: SDG name is required.
    if not data.get('name'):
        errors.append('SDG name is required')
    
    # Check 2: SDG number is required and must be an integer between 1 and 17.
    if not data.get('number'):
        errors.append('SDG number is required')
    else:
        try:
            number = int(data['number'])
            if not (1 <= number <= 17): # SDGs are typically numbered 1-17.
                errors.append('SDG number must be between 1 and 17')
        except ValueError:
            errors.append('SDG number must be a valid integer') # Error if not convertible to int.
    
    # Check 3: SDG color code format (must be a 6-digit hex color code, e.g., #RRGGBB).
    if data.get('color_code'):
        if not re.match(r'^#[0-9A-Fa-f]{6}$', data['color_code']):
            errors.append('Color code must be a valid hex color (e.g., #FF5733)')
    
    return errors

def validate_question_data(data):
    """
    Validates question form data for SDG assessment questions.

    Checks for required fields (text, SDG ID, type) and constraints related to
    options (for 'checklist' type) and max_score.

    Args:
        data (dict): A dictionary containing question attributes.
                     Expected keys: 'question_text', 'primary_sdg_id', 'question_type',
                                    'options' (if checklist), 'max_score'.

    Returns:
        list[str]: A list of error messages. Empty if all validations pass.
    """
    errors = []
    
    # Check 1: Question text is required.
    if not data.get('question_text'):
        errors.append('Question text is required')
    
    # Check 2: Primary SDG ID (linking question to an SDG) is required.
    if not data.get('primary_sdg_id'):
        errors.append('Primary SDG is required') # Should also validate if it's a valid existing SDG ID.
    
    # Check 3: Question type is required and must be one of the predefined valid types.
    if not data.get('question_type'):
        errors.append('Question type is required')
    elif data['question_type'] not in ['select', 'checklist', 'text']: # Define valid types.
        errors.append('Invalid question type')
    
    # Check 4: Options validation for 'checklist' type questions.
    # Options should be a list of objects, each with at least a 'text' property.
    if data.get('question_type') == 'checklist' and data.get('options'):
        try:
            # Options might come as a JSON string or already parsed list/dict.
            options_data = json.loads(data['options']) if isinstance(data['options'], str) else data['options']
            if not isinstance(options_data, list):
                errors.append('Options must be a list')
            else:
                for option in options_data:
                    # Each option in the list should be a dictionary with a 'text' key.
                    if not isinstance(option, dict) or 'text' not in option:
                        errors.append('Each option must be an object with at least a "text" property')
        except json.JSONDecodeError: # Handle if 'options' is a string but not valid JSON.
            errors.append('Options must be valid JSON')
    
    # Check 5: Max score validation.
    if data.get('max_score'):
        try:
            max_score = float(data['max_score']) # Max score should be a number.
            if max_score <= 0: # Max score should be positive.
                errors.append('Max score must be a positive number')
        except ValueError:
            errors.append('Max score must be a valid number') # Error if not convertible to float.
    
    return errors

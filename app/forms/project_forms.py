from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, FloatField, DateField
from wtforms.validators import DataRequired, Length, NumberRange, Optional, ValidationError
from datetime import datetime

class DateAfterValidator:
    """Validates that a date field occurs after another date field."""
    
    def __init__(self, other_field_name, message=None):
        self.other_field_name = other_field_name
        self.message = message or 'End date must be after start date'
        
    def __call__(self, form, field):
        try:
            other_field = form._fields.get(self.other_field_name)
            if other_field is None:
                raise ValidationError(f"Referenced field '{self.other_field_name}' does not exist in form.")
            
            if field.data and other_field.data and field.data <= other_field.data:
                raise ValidationError(self.message)
        except KeyError:
            raise ValidationError(f"Referenced field '{self.other_field_name}' does not exist in form.")

class ProjectForm(FlaskForm):
    name = StringField('Project Name', validators=[
        DataRequired(message='Project name is required'),
        Length(max=100, message='Project name must be less than 100 characters')
    ])
    
    description = TextAreaField('Description', validators=[
        Optional(),
        Length(max=500, message='Description must be less than 500 characters')
    ])
    
    project_type = SelectField('Project Type', validators=[
        DataRequired(message='Project type is required')
    ], choices=[
        ('residential', 'Residential'),
        ('commercial', 'Commercial'),
        ('mixed_use', 'Mixed Use'),
        ('public', 'Public'),
        ('educational', 'Educational'),
        ('healthcare', 'Healthcare'),
        ('industrial', 'Industrial'),
        ('infrastructure', 'Infrastructure'),
        ('landscape', 'Landscape'),
        ('urban_planning', 'Urban Planning'),
        ('other', 'Other')
    ])
    
    location = StringField('Location', validators=[
        DataRequired(message='Location is required'),
        Length(max=255, message='Location must be less than 255 characters')
    ])
    
    size_sqm = FloatField('Size (sqm)', validators=[
        Optional(),
        NumberRange(min=0.1, max=1000000, message='Size must be a positive number less than 1,000,000 sq meters')
    ])
    
    start_date = DateField('Start Date', validators=[
        Optional()
    ], format='%Y-%m-%d')
    
    end_date = DateField('End Date', validators=[
        Optional(),
        DateAfterValidator('start_date')
    ], format='%Y-%m-%d')
    
    budget = FloatField('Budget', validators=[
        Optional(),
        NumberRange(min=0.1, message='Budget must be a positive number')
    ])
    
    sector = SelectField('Sector', validators=[
        Optional()
    ], choices=[
        ('', 'Select a Sector (Optional)'),
        ('residential', 'Residential'),
        ('commercial', 'Commercial'),
        ('education', 'Education'),
        ('healthcare', 'Healthcare'),
        ('transportation', 'Transportation'),
        ('technology', 'Technology'),
        ('energy', 'Energy'),
        ('industrial', 'Industrial'),
        ('agriculture', 'Agriculture'),
        ('entertainment', 'Entertainment'),
        ('hospitality', 'Hospitality'),
        ('public', 'Public'),
        ('other', 'Other')
    ]) 
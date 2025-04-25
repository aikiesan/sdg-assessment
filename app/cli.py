"""
Flask CLI commands for database management.
"""

import click
from flask.cli import with_appcontext
from app import db
from app.utils.db import get_db

@click.command('init-sdg-data')
@with_appcontext
def init_sdg_data_command():
    """Initialize SDG data in the database."""
    from app.models.sdg import SdgGoal
    
    try:
        # Check if SDG goals already exist
        existing = SdgGoal.query.count()
        if existing > 0:
            click.echo(f'SDG data already exists ({existing} goals found).')
            return
        
        # Define the 17 SDGs
        sdgs = [
            {'number': 1, 'name': 'No Poverty', 'color_code': '#e5243b'},
            {'number': 2, 'name': 'Zero Hunger', 'color_code': '#dda63a'},
            # ... remaining SDGs
        ]
        
        # Insert SDGs
        for sdg in sdgs:
            new_sdg = SdgGoal(**sdg)
            db.session.add(new_sdg)
        
        db.session.commit()
        click.echo(f'Successfully initialized {len(sdgs)} SDG goals.')
    
    except Exception as e:
        db.session.rollback()
        click.echo(f'Error initializing SDG data: {str(e)}')

def register_cli_commands(app):
    """Register CLI commands with the Flask app."""
    app.cli.add_command(init_sdg_data_command)
    # Add other commands here
